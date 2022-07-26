import logging
from datetime import datetime

from django.db import models
from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.utils import timezone
from django.conf import settings

from cache_memoize import cache_memoize
from hashids import Hashids

from mail_templated import send_mail


HASHIDS_LENGTH = 12
# NOTE: we may have to strip the : between UTC offset hours and minutes.
#       see: https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
# 2022-07-22T02:45:35+00:00
DATETIME_FMT = '%Y-%m-%dT%H:%M:%S%z'

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


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
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    username = models.CharField(max_length=32)
    email = models.EmailField('email address', unique=True)
    is_confirmed = models.BooleanField(default=False)

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


class Platform(HashidsModelMixin, models.Model):
    users = models.ManyToManyField(User, through='UserPlatform')
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField(unique=True)
    options = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return self.name


class Channel(HashidsModelMixin, models.Model):
    platform = models.ForeignKey(
        Platform, related_name='channels', on_delete=models.CASCADE)
    users = models.ManyToManyField(
        User, through='UserChannel', related_name='channels')
    name = models.CharField(max_length=64, unique=True)
    url = models.URLField()
    options = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return self.name


class VideoManager(HashidsManagerMixin, models.Manager):
    @atomic
    def from_json(self, channel, json):
        title = json['title'].title()
        poster = json['i']
        duration = json.get('duration')
        fps = json.get('fps')
        published = maybe_parse_date(json.get('pubDate'))

        video, created = self.get_or_create(
            platform=channel.platform, channel=channel, title=title,
            poster=poster, defaults={
                'published': published, 'duration': duration, 'fps': fps
            }
        )
        if created:
            sources = VideoSource.objects.from_json(video, json)

        return video


class Video(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('platform', 'channel', 'title', 'poster')
        ]

    platform = models.ForeignKey(
        Platform, related_name='videos', on_delete=models.CASCADE)
    channel = models.ForeignKey(
        Channel, related_name='videos', on_delete=models.CASCADE)
    users = models.ManyToManyField(
        User, through='UserVideo', related_name='videos')
    title = models.CharField(max_length=256)
    poster = models.URLField()
    duration = models.PositiveIntegerField()
    fps = models.PositiveSmallIntegerField()
    published = models.DateTimeField(default=timezone.now)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = VideoManager()

    def __str__(self):
        return self.title

    @cached_property
    def num_plays(self):
        return self.plays.count()

    @cached_property
    def num_likes(self):
        return self.likes.count()

    @cached_property
    def num_dislikes(self):
        return self.dislikes.count()


class VideoSourceManager(HashidsManagerMixin, models.Manager):
    def from_json(self, video, json):
        dims = json['ua']['mp4']

        for dim, props in dims.items():
            height = dim
            width = props['meta']['w']
            url = props['url']

            VideoSource.objects.update_or_create(
                video=video, width=width, height=height, defaults={'url': url}
            )


class VideoSource(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('video', 'width', 'height'),
        ]

    video = models.ForeignKey(
        Video, related_name='sources', on_delete=models.CASCADE)
    width = models.PositiveSmallIntegerField()
    height = models.PositiveSmallIntegerField()
    url = models.URLField(unique=True)

    objects = VideoSourceManager()

    def __str__(self):
        return self.dimension

    @property
    def dimension(self):
        return f'{self.width}x{self.height}'


class UserPlatform(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'platform'),
        ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    params = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return f'{self.user}: {self.platform}'


class UserChannel(HashidsModelMixin, models.Model):
    class Meta:
        unique_together = [
            ('user', 'channel'),
        ]
    user = models.ForeignKey(
        User, related_name='subscriptions', on_delete=models.CASCADE)
    channel = models.ForeignKey(
        Channel, related_name='subscribers', on_delete=models.CASCADE)
    cursor = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = HashidsManager()

    def __str__(self):
        return f'{self.user}: {self.channel}'


class UserVideo(models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='played', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='plays', on_delete=models.CASCADE)
    played = models.DateTimeField(default=None, null=True)
    cursor = models.JSONField()
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


class UserDislike(models.Model):
    class Meta:
        unique_together = [
            ('user', 'video'),
        ]

    user = models.ForeignKey(
        User, related_name='disliked', on_delete=models.CASCADE)
    video = models.ForeignKey(
        Video, related_name='dislikes', on_delete=models.CASCADE)
