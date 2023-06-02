import logging
import inspect
import uuid
import string
import random
import json
import time
from os.path import splitext
from datetime import timedelta
from dataclasses import asdict

import sass
from csscompressor import compress

from django import forms
from django.db import models
from django.db.models import Exists, Count, OuterRef, Subquery, Func, F, Q
from django.db.transaction import atomic
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.template import Context
from django.template.loader import get_template
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.sites.models import Site
from django.utils.functional import cached_property
from django.utils.encoding import force_str
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.conf import settings
from django.db.models.fields.json import KeyTransform

from nacl_encrypted_fields.fields import NaClJSONField
from picklefield.fields import PickledObjectField
from cache_memoize import cache_memoize
from hashids import Hashids
from colorfield.fields import ColorField
from mail_templated import send_mail
from bitfield import BitField
from django_celery_beat.models import PeriodicTask

from authlib.oauth2.rfc6749 import (
    ClientMixin, TokenMixin, AuthorizationCodeMixin,
)


HASHIDS_LENGTH = 12
MENU_ITEMS = [
    ('options', 'Options'),
    ('subscriptions', 'Subscriptions'),
    ('again', 'Watch again'),
    ('latest', 'Latest'),
    ('oldies', 'Oldies'),
    ('home', 'Home'),
    ('search', 'Search'),
    ('resume', 'Resume'),
    ('login', 'Login'),
]
AUTH_TYPES = [
    ('password', 'password'),
    ('device_code', 'device_code'),
]
GRANT_TYPES = [
    ('authorization_code', 'authorization_code'),
    ('refresh_token', 'refresh_token'),
    ('password', 'password'),
    ('urn:ietf:params:oauth:grant-type:device_code', 'urn:ietf:params:oauth:grant-type:device_code'),
]
SCHEME_COLORS = {
    'light': {
        'scheme_main': '#ffffff',
        'scheme_main_bis': '#fafafa',
        'scheme_main_ter': '#f5f5f5',
        'scheme_invert': '#0a0a0a',
        'scheme_invert_bis': '#121212',
        'scheme_invert_ter': '#242424',
    },
    'dark': {
        'scheme_main': '#363636',
        'scheme_main_bis': '#121212',
        'scheme_main_ter': '#242424',
        'scheme_invert': '#ffffff',
        'scheme_invert_bis': '#fafafa',
        'scheme_invert_ter': '#f5f5f5',
    }
}
SCHEME_NAMES = zip(SCHEME_COLORS.keys(), SCHEME_COLORS.keys())
TOKEN_AUTH_METHODS = [
    ('client_secret_post', 'client_secret_post'),
    ('client_secret_basic', 'client_secret_basic'),
]

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def grant_types_default():
    return [
        gt[0] for gt in GRANT_TYPES
    ]


def get_file_name(instance, filename):
    ext = splitext(filename)[1]
    return f'{uuid.uuid4()}{ext}'


def get_random_code():
    chars = string.ascii_lowercase + string.digits
    selected = set()
    while len(selected) < 8:
        selected.add(random.choice(chars))
    return ''.join(selected)


def get_random_hour():
    return random.randint(0, 23)


def maybe_make_aware(dt):
    if timezone.is_aware(dt):
        return dt
    return timezone.make_aware(dt, timezone=timezone.utc)


class HashidsQuerySet(models.QuerySet):
    def get(self, *args, **kwargs):
        uid = kwargs.pop('uid', None)
        if uid:
            try:
                kwargs['id'] = self.model.hashids().decode(uid)[0]

            except IndexError:
                LOGGER.exception('Error decoding hashid')
                kwargs['id'] = None
        return super().get(*args, **kwargs)

    def filter(self, *args, **kwargs):
        uid = kwargs.pop('uid', None)
        if uid:
            try:
                kwargs['id'] = self.model.hashids().decode(uid)[0]

            except IndexError:
                LOGGER.exception('Error decoding hashid')
                kwargs['id'] = None
        return super().filter(*args, **kwargs)


class HashidsManagerMixin:
    def get_queryset(self):
        return HashidsQuerySet(
            model=self.model, using=self._db, hints=self._hints)


class HashidsManager(HashidsManagerMixin, models.Manager):
    pass


class HashidsModelMixin:
    @classmethod
    def hashids(cls):
        hashids = getattr(cls, '_hashids', None)
        if not hashids:
            hashids = Hashids(
                min_length=HASHIDS_LENGTH, salt=f'{cls.__name__}:{settings.SECRET_KEY}')
            setattr(cls, '_hashids', hashids)
        return hashids

    @property
    def uid(self):
        return self.hashids().encode(self.id)


class CreatedUpdatedMixin(models.Model):
    class Meta:
        abstract = True

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.
    Uses Django's Postgres ArrayField
    and a MultipleChoiceField for its formfield.
    """

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.MultipleChoiceField,
            'choices': self.base_field.choices,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't
        # care for it.
        # pylint:disable=bad-super-call
        return super(ArrayField, self).formfield(**defaults)


class ModuleAttributeField(models.CharField):
    def __init__(self, module_name, *args, **kwargs):
        self.module_name = module_name
        kwargs['choices'] = self._get_choices()
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['module_name'] = self.module_name
        return name, path, args, kwargs

    @property
    def module(self):
        prefix, _, name = self.module_name.rpartition('.')
        return getattr(__import__(prefix, globals(), locals(), [name], 0), name)

    def _get_choices(self):
        choices = [
            s for s in dir(self.module) if not s.startswith('__')
        ]
        return [
            (c, c) for c in choices if inspect.isclass(getattr(self.module, c))
        ]

    def get_klass(self, value):
        return getattr(self.module, value)

    def to_python(self, value):
        if inspect.isclass(value):
            return value.__name__
        if value is None:
            return value
        return value


class UserManager(HashidsManagerMixin, BaseUserManager):
    def create_user(self, email, password, **kwargs):
        kwargs.setdefault('is_active', False)
        email = self.normalize_email(email)
        user = self.model(email=email, **kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **kwargs):
        kwargs.setdefault('is_staff', True)
        kwargs.setdefault('is_active', True)
        kwargs.setdefault('is_superuser', True)
        kwargs.setdefault('is_confirmed', True)

        if kwargs['is_staff'] is not True:
            raise ValueError('is_staff must be True')
        if kwargs['is_superuser'] is not True:
            raise ValueError('is_superuser must be True')

        return self.create_user(email, password, **kwargs)


class User(HashidsModelMixin, CreatedUpdatedMixin, AbstractUser):
    class Meta:
        unique_together = [
            ('email', 'site', ),
        ]

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=32, unique=True)
    email = models.EmailField('email address', unique=False)
    is_confirmed = models.BooleanField(default=False)
    site = models.ForeignKey(
        Site, related_name='users', on_delete=models.CASCADE)

    objects = UserManager()

    def __str__(self):
        return self.username

    def generate_confirmation(self, ts=None):
        email = self.email
        if ts is None:
            ts = time.time()
        key = settings.SECRET_KEY.encode('utf8')
        message = b'%i--%s' % (ts, email.encode('utf8'))
        signature = binascii.hexlify(hmac.digest(key, message, 'sha256'))
        return {
            'email': email,
            'ts': ts,
            'signature': signature,
        }

    def send_confirmation_email(self, request):
        params = self.generate_confirmation()
        url = request.build_absolute_uri(
            reverse('user-confirm', kwargs={'uid': self.uid}))
        url += '?' + urlencode(params)
        send_mail(
            'email/user_confirmation.eml',
            { 'url': url },
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
        )

    def validate_confirmation(self, ts, signature):
        params = self.generate_confirmation(ts)
        sig1 = binascii.unhexlify(params['signature'])
        sig2 = binascii.unhexlify(signature)
        if time.time() - ts > settings.EMAIL_CONFIRM_DAYS * 86400:
            raise ValueError('Signature expired')
        if not hmac.compare_digest(sig1, sig2):
            raise ValueError('Invalid signature')
        return True


class StripeAccount(CreatedUpdatedMixin, models.Model):
    user = models.OneToOneField(
        User, related_name='stripe_account', on_delete=models.CASCADE)
    account_id = models.CharField(max_length=255)
    access_token = models.CharField(max_length=255)
    refresh_token = models.CharField(max_length=255)


class Brand(HashidsModelMixin, CreatedUpdatedMixin, models.Model):
    user = models.ForeignKey(
        User, related_name='brands', on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    scheme = models.CharField(
        max_length=5, choices=SCHEME_NAMES, default='light')
    theme_css = models.FileField(
        validators=[FileExtensionValidator(allowed_extensions=['css'])])
    favicon = models.ImageField(
        upload_to=get_file_name,
        validators=[FileExtensionValidator(allowed_extensions=['ico', 'png'])],
        null=True)
    logo = models.ImageField(upload_to=get_file_name)
    primary = ColorField(default='#8c67ef', verbose_name='Primary color')
    info = ColorField(default='#3e8ed0', verbose_name='Informative dialogs / text')
    success = ColorField(default='#48c78e', verbose_name='Success dialogs / text')
    warning = ColorField(default='#ffe08a', verbose_name='Warning dialogs / text')
    danger = ColorField(default='#f14668', verbose_name='Danger dialogs / text')

    def __str__(self):
        return f'{self.name}'

    def compile(self, template_name='theme.scss', minify=None):
        if minify is None:
            minify = settings.DJANGO_CSS_MINIFY
        brand = {
            'primary': self.primary,
            'info': self.info,
            'success': self.success,
            'warning': self.warning,
            'danger': self.danger,
            'logo': {
                'url': self.logo.url,
            }
        }
        brand.update(SCHEME_COLORS[self.scheme])
        template = get_template(template_name)
        rendered = template.render({ 'brand': brand })
        css = sass.compile(
            string=rendered, include_paths=[settings.DJANGO_SCSS_PATH])
        if minify:
            css = compress(css)
        return css

    def save(self, *args, **kwargs):
        css = self.compile()
        self.theme_css = ContentFile(css, name=f'{uuid.uuid4()}.css')
        return super().save(*args, **kwargs)


class SiteOption(CreatedUpdatedMixin, models.Model):
    site = models.OneToOneField(
        Site, related_name='options', on_delete=models.CASCADE)
    title = models.CharField('app title', max_length=64, null=True, blank=True)
    brand = models.ForeignKey(
        Brand, null=True, blank=True, related_name='sites',
        on_delete=models.CASCADE)
    default_lang = models.CharField(max_length=2)
    auth_method = models.CharField(
        max_length=32, choices=AUTH_TYPES, default='password')
    auth_required = models.BooleanField(default=False)
    default_menu_item = models.CharField(
        null=True, blank=True, max_length=16, choices=MENU_ITEMS)

    def __str__(self):
        return f'{self.site.name} options'


class MenuItem(CreatedUpdatedMixin, models.Model):
    option = models.ForeignKey(
        SiteOption, related_name='menu_items', on_delete=models.CASCADE)
    name = models.CharField(
        max_length=16, choices=MENU_ITEMS, help_text='Internal identifier')
    title = models.CharField(
        null=True, blank=True, max_length=24,
        help_text='Title of item in menu')
    sort = models.PositiveSmallIntegerField(
        default=0, help_text='Order of item in menu')


class Package(CreatedUpdatedMixin, models.Model):
    user = models.ForeignKey(
        User, related_name='packages', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    price_ppv = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    price_month = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    price_year = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    price_lifetime = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    options = BitField(flags=[
        ('ppv', 'Pay per view enabled'),
        ('preview_1', 'Grant one free preview'),
        ('preview_3', 'Grant three free previews'),
        ('preview_5', 'Grant five free previews'),
    ])

    def __str__(self):
        return self.name


class ChannelQuerySet(models.QuerySet):
    def default_annotations(self):
        queryset = self.annotate(n_videos=Count('videos'))
        return queryset


class ChannelManager(HashidsManager):
    def get_queryset(self):
        return ChannelQuerySet(self.model, using=self._db)

    def default_annotations(self):
        return self.get_queryset().default_annotations()

    def from_dataclass(self, data):
        defaults = asdict(data)
        extern_id = defaults.pop('extern_id')
        original = defaults.pop('original', None)

        channel, created = self.update_or_create(
            extern_id=extern_id, defaults=defaults)
        channel.set_metadata(original)

    def for_user(self, user, annotate=True):
        queryset = self.all()

        if annotate:
            queryset = queryset.default_annotations()

        if not user.is_authenticated:
            queryset = queryset.filter(is_public=True)

        else:
            # NOTE: we select all channels that relate to a package that the
            # user subscribes to.        
            subbed = Subscription.objects.filter(
                package__channels__id=OuterRef('id'),
                user=user
            )

            queryset = queryset.filter(Exists(subbed) | Q(is_public=True))

        return queryset


class Channel(HashidsModelMixin, CreatedUpdatedMixin, models.Model):
    class Meta:
        indexes = [
            GinIndex(fields=['search'])
        ]

    user = models.ForeignKey(
        User, related_name='channels', on_delete=models.CASCADE)
    task = models.ForeignKey(
        PeriodicTask, null=True, blank=True, related_name='channel',
        on_delete=models.CASCADE)
    packages = models.ManyToManyField(Package, related_name='channels')
    extern_id = models.CharField(max_length=128, unique=True)
    options = BitField(flags=[])
    url = models.URLField()
    state = PickledObjectField(null=True, blank=True)
    auth_params = models.JSONField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    name = models.CharField(max_length=64)
    title = models.CharField(max_length=128, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    poster = models.ImageField(null=True, blank=True)
    search = SearchVectorField(null=True)

    objects = ChannelManager()

    def __str__(self):
        return self.name

    def set_metadata(self, metadata=None):
        if metadata is None:
            return

        ChannelMeta.update_or_create(
            video=self, defaults={'metadata': metadata})

    def update(self, **kwargs):
        Channel.objects.filter(id=self.id).update(**kwargs)
    
    def from_dataclass(self, data):
        defaults = asdict(data)
        original = defaults.pop('original', None)

        for key, value in defaults.items():
            # Don't overwrite existing values, but fill in anything missing.
            if getattr(self, key) is not None:
                continue
            setattr(self, key, value)

        self.save()
        self.set_metadata(original)


class ChannelMeta(CreatedUpdatedMixin, models.Model):
    # We don't often need the orignal JSON data, it is kept here for archival
    # purposes only in order to not bloat the base table.
    channel = models.ForeignKey(
        Channel, related_name='meta', on_delete=models.CASCADE)
    metadata = models.JSONField()


class TagQuerySet(models.QuerySet):
    def default_annotations(self):
        queryset = self.annotate(n_tagged=Count('tagged'))
        return queryset

    # NOTE: read-only model, should not be modified once created.
    def update(self, *args, **kwargs):
        raise NotImplementedError('Tags are immutable.')

    def delete(self, *args, **kwargs):
        raise NotImplementedError('Tags are immutable.')


class TagManager(models.Manager):   
    def get_queryset(self):
        return TagQuerySet(self.model, using=self._db)

    def default_annotations(self):
        return self.get_queryset().default_annotations()

    def add_to(self, obj, tags):
        for name in tags:
            obj.tags.add(self.get_or_create(name=name)[0].pk)
            LOGGER.debug('Added tag %s to %s', name, obj)

    def remove_from(self, obj, tags=None):
        if tags is None:
            obj.tags.clear()
            LOGGER.debug('Removed all tags from %s', obj)
            return

        for name in tags:
            try:
                obj.tags.remove(Tag.objects.get(name=name))
            except Tag.DoesNotExist:
                pass
            else:
                LOGGER.debug('Removed tag %s from %s', name, obj)

    def merge_to(self, obj, tags=None):
        if tags is None:
            obj.tags.clear()
            LOGGER.debug('Removed all tags from %s', obj)
            return

        e, n = set(obj.tags.all().values_list('name', flat=True)), set(tags)

        self.add_to(obj, n.difference(e))
        self.remove_from(obj, e.difference(n))


class Tag(models.Model):
    # TODO: make immutable.
    name = models.TextField(
        max_length=32, null=False, unique=True, db_collation='ci')

    objects = TagManager()

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # NOTE: should not be modified once created.
        if self.pk and 'force_insert' not in kwargs:
            raise NotImplementedError('Tags are immutable.')
        return super().save(*args, **kwargs)


class VideoQuerySet(models.QuerySet):
    def default_annotations(self, user=None):
        queryset = self.annotate(
                n_plays=Count('plays'),
                n_likes=Count('likes'),
                n_dislikes=Count('dislikes'),
            )

        if user and user.is_authenticated:
            queryset = queryset.annotate(
                is_played=Exists(
                    Play.objects.filter(
                        video_id=OuterRef('pk'),
                        user=user)
                ),
                is_liked=Exists(
                    Like.objects.filter(
                        video_id=OuterRef('pk'),
                        user=user)
                ),
                is_disliked=Exists(
                    Dislike.objects.filter(
                        video_id=OuterRef('pk'),
                        user=user)
                ),
            )

        return queryset


class VideoManager(HashidsManager):
    def get_queryset(self):
        return VideoQuerySet(
            model=self.model, using=self._db, hints=self._hints)

    def default_annotations(self):
        return self.get_queryset().default_annotations()

    def from_dataclass(self, channel, data):
        defaults = asdict(data)
        extern_id = defaults.pop('extern_id')

        # Used later in separate models.
        tags = defaults.pop('tags')
        original = defaults.pop('original')
        # Must be handled specially
        del defaults['sources']

        # Convert naive datetime to UTC
        defaults['published'] = maybe_make_aware(defaults['published'])

        video, created = Video.objects.update_or_create(
            channel=channel, extern_id=extern_id, defaults=defaults)

        Tag.objects.merge_to(video, tags)
        video.set_metadata(original)
        VideoSource.objects.from_dataclass(video, data.sources)

        return video, created

    def for_user(self, user, annotated=False):
        queryset = self.all()

        if annotated:
            queryset = queryset.default_annotations(user=user)

        if not user.is_authenticated:
            queryset = queryset.filter(channel__is_public=True)

        else:
            subbed = Subscription.objects.filter(
                package__channels__id=OuterRef('channel_id'),
                user=user
            )

            queryset = queryset.filter(Exists(subbed) | Q(is_public=True))

        return queryset


class Video(HashidsModelMixin, CreatedUpdatedMixin, models.Model):
    class Meta:
        indexes = [
            GinIndex(fields=['search']),
        ]

    tags = models.ManyToManyField(Tag, related_name='tagged', blank=True)
    channel = models.ForeignKey(
        Channel, related_name='videos', on_delete=models.CASCADE)
    extern_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=256)
    description = models.TextField(null=True, blank=True)
    poster = models.URLField()
    duration = models.PositiveIntegerField()
    published = models.DateTimeField(default=timezone.now)
    search = SearchVectorField(null=True)

    objects = VideoManager()

    def __str__(self):
        return self.title

    def set_metadata(self, metadata=None):
        if metadata is None:
            return
        VideoMeta.objects.update_or_create(
            video=self, defaults={'metadata': metadata})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for src in self.sources.all():
            src.video_id = self.id
            src.save()


class VideoMeta(CreatedUpdatedMixin, models.Model):
    # We don't often need the orignal JSON data, it is kept here for archival
    # purposes only in order to not bloat the base table.
    video = models.ForeignKey(
        Video, related_name='meta', on_delete=models.CASCADE)
    metadata = models.JSONField()


class VideoSourceManager(HashidsManager):
    def from_dataclass(self, video, datas):
        try:
            iter(datas)
        except:
            datas = [datas]
        
        for data in datas:
            defaults = asdict(data)
            original = defaults.pop('original')
            extern_id = defaults.pop('extern_id')
            url = defaults.pop('url')

            video_source, created = VideoSource.objects.update_or_create(
                video=video,
                extern_id=extern_id,
                url=url,
                defaults=defaults,
            )
            video_source.set_metadata(original)


class VideoSource(HashidsModelMixin, CreatedUpdatedMixin, models.Model):
    class Meta:
        unique_together = [
            ('video', 'extern_id'),
            ('video', 'url'),
        ]

    video = models.ForeignKey(
        Video, related_name='sources', on_delete=models.CASCADE)
    extern_id = models.CharField(max_length=128)
    width = models.PositiveSmallIntegerField(null=True, blank=True)
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    fps = models.PositiveSmallIntegerField(null=True, blank=True)
    size = models.PositiveBigIntegerField(null=True, blank=True)
    mime = models.CharField(max_length=64, null=True, blank=True)
    url = models.URLField(max_length=256)

    objects = VideoSourceManager()

    def __str__(self):
        return self.dimension

    def set_metadata(self, metadata=None):
        if metadata is None:
            return
        VideoSourceMeta.objects.update_or_create(
            video_source=self, defaults={'metadata': metadata})

    @property
    def dimension(self):
        width = str(self.width) if self.width else ''
        height = f'x{self.height}' if self.height else ''
        return f'{width}{height}'


class VideoSourceMeta(CreatedUpdatedMixin, models.Model):
    # We don't often need the orignal JSON data, it is kept here for archival
    # purposes only in order to not bloat the base table.
    video_source = models.ForeignKey(
        VideoSource, related_name='meta', on_delete=models.CASCADE)
    metadata = models.JSONField()


class Subscription(HashidsModelMixin, CreatedUpdatedMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'package'),
        ]

    user = models.ForeignKey(
        User, related_name='subscribed', on_delete=models.CASCADE)
    package = models.ForeignKey(
        Package, related_name='subscriptions', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)
    options = BitField(flags=[
        ('notify', 'Notify me of new videos'),
    ])

    def __str__(self):
        return f'{self.user}: {self.package}'


# class SubscriptionVideo(CreatedUpdatedMixin, models.Model):
#     class Meta:
#         unique_together = [
#             ('video', 'subscription'),
#         ]

#     video = models.ForeignKey(
#         Video, related_name='channels', on_delete=models.CASCADE)
#     subscription = models.ForeignKey(
#         Subscription, related_name='videos', on_delete=models.CASCADE)

#     def __str__(self):
#         return f'{self.channel}: {self.video}'


class Play(CreatedUpdatedMixin, models.Model):
    user = models.ForeignKey(
        User, related_name='played', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='plays', on_delete=models.CASCADE)
    cursor = models.JSONField(null=True, blank=True)

    objects = models.Manager()

    def __str__(self):
        return f'{self.user} played {self.video}'


class Like(CreatedUpdatedMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='liked', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='likes', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        Dislike.objects.filter(user=self.user, video=self.video).delete()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} liked {self.video}'


class Dislike(CreatedUpdatedMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='disliked', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='dislikes', on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        Like.objects.filter(user=self.user, video=self.video).delete()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user} disliked {self.video}'


class QueueManager(models.Manager):
    @atomic
    def prepend(self, obj):
        self.filter(user=obj.user) \
            .update(position=F('position') + 1)
        obj.position = 0
        obj.save(force_insert=True)
        obj.refresh_from_db()
        return obj

    @atomic
    def append(self, obj):
        # NOTE: Purposely did not use .count() here as that would be fragile in
        # case there are gaps in our position values.
        try:
            obj.position = self \
                .select_for_update() \
                .filter(user=obj.user) \
                .aggregate(Max('position')) \
                .values_list('position__max', flat=True)[0] + 1

        except IndexError:
            obj.position = 0
        obj.save(force_insert=True)
        obj.refresh_from_db()
        return obj

    @atomic
    def remove(self, obj):
        position = obj.position
        obj.delete()
        self.filter(user=obj.user, position__gt=position) \
            .update(position=F['position'] - 1)


class Queue(CreatedUpdatedMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
            ('user', 'position'),
        ]

    user = models.ForeignKey(
        User, related_name='queued', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='queued', on_delete=models.CASCADE)
    position = models.PositiveSmallIntegerField(default=0)

    objects = QueueManager()


# https://docs.authlib.org/en/latest/django/2/authorization-server.html
class OAuth2Client(HashidsModelMixin, models.Model, ClientMixin):
    class Meta:
        verbose_name = "OAuth2 Client"

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client_id = models.UUIDField(unique=True, default=uuid.uuid4, blank=True)
    client_secret = models.UUIDField(null=False, default=uuid.uuid4, blank=True)
    client_name = models.CharField(max_length=120)
    website_uri = models.URLField(max_length=256, null=True)
    description = models.TextField(null=True)
    redirect_uris = ArrayField(models.CharField(max_length=256))
    default_redirect_uri = models.CharField(max_length=256, null=True)
    scope = ArrayField(models.CharField(max_length=24), null=True)
    response_types = ArrayField(models.CharField(max_length=32), null=True)
    grant_types = ChoiceArrayField(
        models.CharField(max_length=48, choices=GRANT_TYPES),
        null=False,
        default=grant_types_default
    )
    token_endpoint_auth_method = models.CharField(
        choices=TOKEN_AUTH_METHODS, max_length=120, null=False,
        default='client_secret_post')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def get_client_id(self):
        return str(self.client_id)

    def get_default_redirect_uri(self):
        return self.default_redirect_uri

    def get_allowed_scope(self, scope):
        if not scope:
            return []
        return [s for s in scope if s in self.scope]

    def check_redirect_uri(self, redirect_uri):
        if redirect_uri == self.default_redirect_uri:
            return True
        return redirect_uri in self.redirect_uris

    def has_client_secret(self):
        return bool(self.client_secret)

    def check_client_secret(self, client_secret):
        return str(self.client_secret) == client_secret

    def check_endpoint_auth_method(self, method, endpoint):
        return endpoint != 'token' or self.token_endpoint_auth_method == method

    def check_response_type(self, response_type):
        return response_type in self.response_types

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types
        return allowed


class OAuth2Token(HashidsModelMixin, models.Model, TokenMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(
        OAuth2Client, to_field="client_id", db_column="client", on_delete=models.CASCADE)
    token_type = models.CharField(max_length=40)
    access_token = models.CharField(max_length=255, unique=True, null=False)
    refresh_token = models.CharField(max_length=255, db_index=True, null=False)
    scope = ArrayField(models.CharField(max_length=24), null=True)
    revoked = models.BooleanField(default=False)
    expires_in = models.IntegerField(null=False, default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def get_client_id(self):
        return self.client.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.created + timedelta(seconds=self.expires_in)


class OAuth2Code(HashidsModelMixin, models.Model, AuthorizationCodeMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(
        OAuth2Client, to_field="client_id", db_column="client", on_delete=models.CASCADE)
    code = models.CharField(max_length=120, unique=True, null=False)
    redirect_uri = models.TextField(null=True)
    response_type = models.TextField(null=True)
    scope = ArrayField(models.CharField(max_length=24), null=True)
    nonce = models.CharField(max_length=120, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def is_expired(self):
        return self.created + timedelta(seconds=300) < timezone.now()

    def get_redirect_uri(self):
        return self.redirect_uri

    def get_scope(self):
        return self.scope

    def get_auth_time(self):
        return self.auth_time.timestamp()

    def get_nonce(self):
        return self.nonce


class OAuth2DeviceCode(models.Model):
    client = models.ForeignKey(
        OAuth2Client, related_name='device_codes', on_delete=models.CASCADE)
    user = models.ForeignKey(
        User, null=True, related_name='devices_codes', on_delete=models.CASCADE)
    scope = ArrayField(models.CharField(max_length=24), null=True)
    device_code = models.CharField(max_length=42)
    user_code = models.CharField(max_length=9, unique=True)
    expires_in = models.PositiveSmallIntegerField(default=300)
    allowed = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def is_expired(self):
        return self.created + timedelta(seconds=self.expires_in) < timezone.now()

    def get_client_id(self):
        return str(self.client.client_id)

    def get_user_code(self):
        return str(self.user_code)

    def get_scope(self):
        return self.scope
