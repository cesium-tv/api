from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_recaptcha.fields import ReCaptchaV2Field

from rest.models import (
    Channel, VideoSource, Video,  OAuth2Token, OAuth2Client, OAuth2Code, Play,
    Like, Dislike,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('uid', 'username', 'email', 'password', 'created')
        extra_kwargs = {
            'password': {'write_only': True},
        }

    uid = serializers.CharField(read_only=True)

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
            k: v for k, v in validated_data.items()
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


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = ('uid', 'name', 'url', 'videos', 'subscribers', 'created')

    uid = serializers.CharField(read_only=True)
    videos = serializers.IntegerField(source='num_videos')
    subscribers = serializers.IntegerField(source='num_subscribers')


class VideoSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSource
        fields = ('uid', 'width', 'height', 'url', 'fps', 'size', 'created')

    uid = serializers.CharField(read_only=True)


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = (
            'uid', 'channel', 'title', 'poster', 'duration', 'published',
            'sources', 'total_plays', 'total_likes', 'total_dislikes', 'liked',
            'disliked', 'played', 'created',
        )

    uid = serializers.CharField(read_only=True)
    channel = ChannelSerializer()
    sources = serializers.SerializerMethodField()
    played = serializers.SerializerMethodField()
    liked = serializers.SerializerMethodField()
    disliked = serializers.SerializerMethodField()
    plays = serializers.SerializerMethodField()
    likes = serializers.SerializerMethodField()
    dislikes = serializers.SerializerMethodField()

    def get_sources(self, obj):
        sources = {}
        for source in obj.sources.all():
            sources[source.dimension] = \
                VideoSourceSerializer(source, many=False).data
        return sources

    def get_played(self, obj):
        return getattr(obj, 'played', None)

    def get_liked(self, obj):
        return getattr(obj, 'liked', None)

    def get_disliked(self, obj):
        return getattr(obj, 'disliked', None)

    def get_plays(self, obj):
        return getattr(obj, 'plays', None)

    def get_likes(self, obj):
        return getattr(obj, 'likes', None)

    def get_dislikes(self, obj):
        return getattr(obj, 'dislikes', None)


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ('uid', 'user', 'video', 'created')

    uid = serializers.CharField(read_only=True)
    user = UserSerializer(many=False)
    video = VideoSerializer(many=False)


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('uid', 'user', 'video', 'created')

    uid = serializers.CharField(read_only=True)
    user = UserSerializer(many=False)
    video = VideoSerializer(many=False)


class DislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dislike
        fields = ('uid', 'user', 'video', 'created')

    uid = serializers.CharField(read_only=True)
    user = UserSerializer(many=False)
    video = VideoSerializer(many=False)


class OAuth2ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAuth2Client
        fields = ('user', 'client_id', 'client_name', 'website_uri',
        'description', 'scope', 'created')

    user = UserSerializer(fields=('uid', 'username',))


class OAuth2TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAuth2Token
        fields = ('uid', 'client', 'token_type', 'scope', 'revoked',
                  'expires_in', 'created')

    uid = serializers.CharField(read_only=True)
    client = OAuth2ClientSerializer()


class OAuth2AuthzCodeSerializer(serializers.Serializer):
    client = OAuth2ClientSerializer()
