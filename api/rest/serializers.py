from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_recaptcha.fields import ReCaptchaV2Field

from rest.models import Publisher, Channel, VideoSource, Video

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uid', 'username', 'email', 'password', 'recaptcha')
        extra_kwargs = {
            'password': {'write_only': True},
            'recaptcha': {'write_only': True},
        }

    uid = serializers.CharField(read_only=True)
    recaptcha = ReCaptchaV2Field()

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        if fields:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    def create(self, validated_data):
        kwargs = {
            k: v for k, v in validated_data.items() if k != 'recaptcha'
        }
        return User.objects.create_user(is_active=False, **kwargs)


class UserConfirmSerializer(serializers.Serializer):
    ts = serializers.FloatField()
    signature = serializers.CharField()

    def __init__(self, uid, *args, **kwargs):
        self.uid = uid
        super().__init__(*args, **kwargs)

    def validate(self, attrs):
        try:
            user = User.objects.get(uid=self.uid)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid signature')
        try:
            user.validate_confirmation(attrs['ts'], attrs['signature'])

        except ValueError as e:
            raise serializers.ValidationError('Invalid signature')
        return attrs

    def create(self, validated_data):
        user = User.objects.get(uid=self.uid)
        user.is_active = True
        user.is_confirmed = True
        return user


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ('uid', 'name', 'url', 'channels')

    uid = serializers.CharField(read_only=True)
    channels = serializers.IntegerField(source='num_channels')


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ('uid', 'name', 'url', 'platform', 'videos', 'subscribers')

    uid = serializers.CharField(read_only=True)
    platform = serializers.SerializerMethodField()
    videos = serializers.IntegerField(source='num_videos')
    subscribers = serializers.IntegerField(source='num_subscribers')

    def get_platform(self, obj):
        return Publisher.hashids().encode(obj.platform_id)


class VideoSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSource
        fields = ('uid', 'dimension', 'url')

    uid = serializers.CharField(read_only=True)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = (
            'uid', 'channel', 'title', 'poster', 'duration', 'fps', 'published',
            'sources', 'plays', 'likes', 'dislikes', 'liked', 'disliked', 'played',
        )

    uid = serializers.CharField(read_only=True)
    channel = serializers.SerializerMethodField()
    sources = serializers.SerializerMethodField()
    plays = serializers.IntegerField(source='num_plays')
    likes = serializers.IntegerField(source='num_likes')
    dislikes = serializers.IntegerField(source='num_dislikes')
    played = serializers.BooleanField()
    liked = serializers.BooleanField()
    disliked = serializers.BooleanField()

    def get_sources(self, obj):
        sources = {}
        for source in obj.sources.all():
            sources[source.dimension] = {
                'url': source.url,
                'width': source.width,
                'height': source.height,
            }
        return sources

    def get_channel(self, obj):
        return Channel.hashids().encode(obj.channel_id)
