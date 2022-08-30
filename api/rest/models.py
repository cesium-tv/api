import logging
import inspect
import uuid
from os.path import splitext
from datetime import datetime

from django import forms
from django.db import models
from django.db.transaction import atomic
from django.core.validators import FileExtensionValidator
from django.contrib.postgres.fields import CITextField, ArrayField
from django.contrib.sites.models import Site
from django.utils.functional import cached_property
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.conf import settings

from cache_memoize import cache_memoize
from hashids import Hashids
from colorfield.fields import ColorField
from mail_templated import send_mail


HASHIDS_LENGTH = 12
DATETIME_FMT = '%Y-%m-%dT%H:%M:%S%z'

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def get_file_name(instance, filename):
    ext = splitext(filename)[1]
    return f'{uuid.uuid4()}.{ext}'


def maybe_parse_date(date_str):
    if date_str is None:
        return None

    try:
        return datetime.strptime(date_str, DATETIME_FMT)

    except ValueError:
        LOGGER.exception('Error parsing datetime')
        return timezone.now()


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


class User(HashidsModelMixin, AbstractUser):
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


class Brand(HashidsModelMixin, models.Model):
    name = models.CharField(max_length=32)
    favicon = models.ImageField(
        upload_to=get_file_name,
        validators=[FileExtensionValidator(allowed_extensions=['ico'])],
        null=True)
    logo = models.ImageField(upload_to=get_file_name)
    bgcolor = ColorField(default='#000000', verbose_name='Background color')
    fgcolor = ColorField(default='#FFFFFF', verbose_name='Foreground color')
    actcolor = ColorField(default='#FFFFFF', verbose_name='Active color')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Brand {self.name}'


class SiteOption(models.Model):
    site = models.OneToOneField(
        Site, related_name='options', on_delete=models.CASCADE)
    title = models.CharField('app title', max_length=64, null=True, blank=True)
    brand = models.ForeignKey(
        Brand, null=True, blank=True, related_name='sites',
        on_delete=models.CASCADE)
    menu = ChoiceArrayField(
        models.CharField(max_length=32, choices=[
            ('options', 'Options'),
            ('subscriptions', 'Subscriptions'),
            ('again', 'Watch again'),
            ('latest', 'Latest'),
            ('oldies', 'Oldies'),
            ('home', 'Home'),
            ('search', 'Search'),
            ('resume', 'Resume'),
        ])
    )
    default_lang = models.CharField(max_length=2)
    auth = ModuleAttributeField(
        'vidsrc.auth', max_length=32, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def AuthClass(self):
        return self._meta.get_field('auth').get_klass(self.auth)

    @property
    def auth_method(self):
        return getattr(self.AuthClass, 'method', None)

    def __str__(self):
        return f'{self.site.name} options'


class Publisher(HashidsModelMixin, models.Model):
    sites = models.ManyToManyField(Site)
    users = models.ManyToManyField(User)
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField()
    options = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return self.name


class Platform(HashidsModelMixin, models.Model):
    name = models.CharField(max_length=64)
    crawler = ModuleAttributeField('vidsrc.crawl', max_length=32)

    @property
    def CrawlerClass(self):
        return self._meta.get_field('crawler').get_klass(self.crawler)


class Channel(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('publisher', 'name'),
        ]

    publisher = models.ForeignKey(
        Publisher, related_name='channels', on_delete=models.CASCADE)
    platform = models.ForeignKey(
        Platform, related_name='channels', on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    url = models.URLField()
    extern_id = models.CharField(max_length=128, unique=True)
    extern_cursor = models.JSONField(null=True, blank=True)
    options = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return self.name

    def update(self, **kwargs):
        Channel.objects.filter(id=self.id).update(**kwargs)


class Tag(models.Model):
    name = CITextField(max_length=32, null=False, unique=True)


class Video(HashidsModelMixin, models.Model):
    channel = models.ForeignKey(
        Channel, related_name='videos', on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, related_name='tagged')
    extern_id = models.CharField(max_length=128, unique=True)
    title = models.CharField(max_length=256)
    poster = models.URLField()
    duration = models.PositiveIntegerField()
    original = models.JSONField(null=True, blank=True)
    total_plays = models.PositiveIntegerField(default=0)
    total_likes = models.PositiveIntegerField(default=0)
    total_dislikes = models.PositiveIntegerField(default=0)
    published = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        for src in self.sources.all():
            src.video_id = self.id
            src.save()


class VideoSource(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('video', 'width', 'height'),
            ('video', 'url'),
        ]

    video = models.ForeignKey(
        Video, related_name='sources', on_delete=models.CASCADE)
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField(null=True, blank=True)
    fps = models.PositiveSmallIntegerField()
    size = models.PositiveBigIntegerField(null=True, blank=True)
    url = models.URLField()
    original = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.dimension

    @property
    def dimension(self):
        height = f'x{self.height}' if self.height else ''
        return f'{self.width}{height}'


class Subscription(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'channel'),
        ]
    user = models.ForeignKey(
        User, related_name='subscribed', on_delete=models.CASCADE)
    channel = models.ForeignKey(
        Channel, related_name='subscribers', on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return f'{self.user}: {self.channel}'


class UserPlay(models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='played', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='plays', on_delete=models.CASCADE)
    cursor = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = models.Manager()

    def __str__(self):
        return f'{self.user}: {self.video}'


class UserLike(models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='liked', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='likes', on_delete=models.CASCADE)
    # +1 for like, -1 for dislike
    like = models.SmallIntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
