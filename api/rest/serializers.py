from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_recaptcha.fields import ReCaptchaV2Field

from rest.models import (
    Channel, VideoSource, Video,  OAuth2Token, OAuth2Client, OAuth2Code, Play,
    Like, Dislike, Subscription, Queue,
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
    email = serializers.SerializerMethodField()

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

    def get_email(self, obj):
        # NOTE: only reveal email for logged in user, no other user's
        # email addresses are provided.
        request = self.context.get('request')
        if request and obj == request.user:
            return obj.email


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
    videos = serializers.SerializerMethodField()
    subscribers = serializers.SerializerMethodField()

    def get_videos(self, obj):
        return Video.objects.filter(channel=obj).count()

    def get_subscribers(self, obj):
        return Subscription.objects.filter(package__channels__in=(obj,)).count()


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
            'sources', 'created', 'is_played', 'is_liked', 'is_disliked',
            'n_plays', 'n_likes', 'n_dislikes',
        )

    uid = serializers.CharField(read_only=True)
    channel = ChannelSerializer(read_only=True)
    sources = VideoSourceSerializer(many=True, read_only=True)
    is_played = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    n_plays = serializers.IntegerField()
    n_likes = serializers.IntegerField()
    n_dislikes = serializers.IntegerField()

    def get_is_played(self, obj):
        return getattr(obj, 'is_played', False)

    def get_is_liked(self, obj):
        return getattr(obj, 'is_liked', False)

    def get_is_disliked(self, obj):
        return getattr(obj, 'is_disliked', False)


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


class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = ('uid', 'user', 'video', 'position', 'created')

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
