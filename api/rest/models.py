import logging
import inspect
import uuid
import string
import random
from os.path import splitext
from datetime import timedelta
from base64 import b64encode

import sass
from csscompressor import compress

from django import forms
from django.db import models
from django.db.models.fields.files import FieldFile
from django.db.transaction import atomic
from django.core.validators import FileExtensionValidator
from django.core.files.base import ContentFile
from django.template import Context
from django.template.loader import get_template
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
from datauri import DataURI

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
        'white': '#ffffff',
        'white_bis': '#fafafa',
        'white_ter': '#f5f5f5',
        'black': '#0a0a0a',
        'black_bis': '#121212',
        'black_ter': '#242424',
    },
    'dark': {
        'white': '#0a0a0a',
        'white_bis': '#121212',
        'white_ter': '#242424',
        'black': '#ffffff',
        'black_bis': '#fafafa',
        'black_ter': '#f5f5f5',
    }
}
SCHEME_NAMES = [(None, None)] + list(
    zip(SCHEME_COLORS.keys(), SCHEME_COLORS.keys()))
THEME_COLORS = {
        'white':         '#ffffff',  # hsl(0, 0%, 100%) !default
        'white_bis':     '#fafafa',  # hsl(0, 0%, 98%) !default
        'white_ter':     '#f5f5f5',  # hsl(0, 0% 96%) !default
        'black':         '#0a0a0a',  # hsl(0, 0%, 4%) !default
        'black_bis':     '#121212',  # hsl(0, 0%, 7%) !default
        'black_ter':     '#242424',  # hsl(0, 0%, 14%) !default

        'grey_darker':   '#363636',  # hsl(0, 0%, 21%) !default
        'grey_dark':     '#4a4a4a',  # hsl(0, 0%, 29%) !default
        'grey':          '#7a7a7a',  # hsl(0, 0%, 48%) !default
        'grey_light':    '#b5b5b5',  # hsl(0, 0%, 71%) !default
        'grey_lighter':  '#dbdbdb',  # hsl(0, 0%, 86%) !default
        'grey_lightest': '#ededed',  # hsl(0, 0%, 93%) !default

        'orange':        '#ff470f',  # hsl(14,  100%, 53%) !default
        'yellow':        '#ffe08a',  # hsl(44,  100%, 77%) !default
        'green':         '#48c78e',  # hsl(153, 53%,  53%) !default
        'turquoise':     '#00d1b2',  # hsl(171, 100%, 41%) !default
        'cyan':          '#3e8ed0',  # hsl(207, 61%,  53%) !default
        'blue':          '#485fc7',  # hsl(229, 53%,  53%) !default
        'purple':        '#b86bff',  # hsl(271, 100%, 71%) !default
        'red':           '#f14668',  # hsl(348, 86%, 61%) !default
}
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



class DataURIImageFieldFile(FieldFile):
    @property
    def data_uri(self):
        self._require_file()
        data_uri = DataURI.from_file(self.path)
        base64 = b64encode(data_uri.data).decode('utf8')
        return f'data:{data_uri.mimetype};base64,{base64}'


class FileField(models.FileField):
    attr_class = DataURIImageFieldFile


class ImageField(models.ImageField):
    attr_class = DataURIImageFieldFile


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
    scheme = models.CharField(
        max_length=5, null=True, blank=True, choices=SCHEME_NAMES)
    theme_css = FileField(
        validators=[FileExtensionValidator(allowed_extensions=['css'])])
    favicon = ImageField(
        upload_to=get_file_name,
        validators=[FileExtensionValidator(allowed_extensions=['ico', 'png'])],
        null=True)
    logo = ImageField(upload_to=get_file_name, null=True, blank=True)
    colors = models.JSONField(default=THEME_COLORS, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'

    def compile(self, template_name='theme.scss', minify=None):
        if minify is None:
            minify = settings.DJANGO_CSS_MINIFY
        template = get_template(template_name)
        rendered = template.render({ 'brand': self })
        css = sass.compile(
            string=rendered, include_paths=[settings.DJANGO_SCSS_PATH])
        if minify:
            css = compress(css)
        return css

    def save(self, *args, **kwargs):
        if self.scheme:
            print('HERE HERE HERE', SCHEME_COLORS[self.scheme])
            self.colors.update(SCHEME_COLORS[self.scheme])
        css = self.compile()
        self.theme_css = ContentFile(css, name=f'{uuid.uuid4()}.css')
        return super().save(*args, **kwargs)


class SiteOption(models.Model):
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
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.site.name} options'


class MenuItem(models.Model):
    option = models.ForeignKey(
        SiteOption, related_name='menu_items', on_delete=models.CASCADE)
    name = models.CharField(
        max_length=16, choices=MENU_ITEMS, help_text='Internal identifier')
    title = models.CharField(
        null=True, blank=True, max_length=24,
        help_text='Title of item in menu')
    sort = models.PositiveSmallIntegerField(
        default=0, help_text='Order of item in menu')


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
    issued_at = models.DateTimeField(null=False, default=timezone.now)
    expires_in = models.IntegerField(null=False, default=0)

    objects = HashidsManager()

    def get_client_id(self):
        return self.client.client_id

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def get_expires_at(self):
        return self.issued_at + timedelta(seconds=self.expires_in)


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
