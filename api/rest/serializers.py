import logging

from django.contrib.auth import get_user_model

from rest_framework import serializers
from drf_recaptcha.fields import ReCaptchaV2Field

from rest.models import (
    Channel, VideoSource, Video,  OAuth2Token, OAuth2Client, OAuth2Code, Play,
    Like, Dislike, Subscription, Queue, Tag, Term,
)


User = get_user_model()

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


class SearchResultSerializer(serializers.Serializer):
    "Serializes as a search result if rank is present on model."
    def to_representation(self, obj):
        obj_repr = self.object_serializer_class(obj).to_representation(obj)
        if hasattr(obj, 'rank'):
            # Search result:
            obj_repr = {
                'rank': obj.rank,
                self.related_name: obj_repr,
            }
            for field_name in self.highlight_fields:
                field_name = f'{field_name}_highlighted'
                obj_repr[field_name] = getattr(obj, field_name)

        return obj_repr


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


class ChannelObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = (
            'uid', 'name', 'url', 'n_subscribers', 'created', 'n_videos',
            'rank', 'snippet',
        )

    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super().__init__(*args, **kwargs)
        for field_name in exclude_fields:
            self.fields.pop(field_name)

    uid = serializers.CharField(read_only=True)
    n_videos = serializers.IntegerField()
    n_subscribers = serializers.IntegerField()
    rank = serializers.FloatField(read_only=True)
    snippet = serializers.CharField(read_only=True)


class ChannelSerializer(SearchResultSerializer):
    related_name = 'channel'
    object_serializer_class = ChannelObjectSerializer
    highlight_fields = ('name', 'title', 'description', 'url')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('uid', 'name', 'n_tagged')

    uid = serializers.CharField(read_only=True)
    n_tagged = serializers.IntegerField()


class TermSerializer(serializers.ModelSerializer):
    class Meta:
        model = Term
        fields = ('uid', 'ngram', 'freq')

    uid = serializers.CharField(read_only=True)


class VideoSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoSource
        fields = (
            'uid', 'width', 'height', 'url', 'mime', 'fps', 'size', 'created',
        )

    uid = serializers.CharField(read_only=True)


class VideoObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = (
            'uid', 'channel', 'title', 'poster', 'duration', 'published',
            'sources', 'tags', 'created', 'cursor', 'is_played', 'is_liked',
            'is_disliked', 'n_plays', 'n_likes', 'n_dislikes',
        )

    uid = serializers.CharField(read_only=True)
    channel = ChannelObjectSerializer(
        read_only=True, exclude_fields=('n_videos', 'n_subscribers'))
    sources = VideoSourceSerializer(many=True, read_only=True)
    tags = serializers.StringRelatedField(many=True)
    cursor = serializers.SerializerMethodField()
    is_played = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_disliked = serializers.SerializerMethodField()
    n_plays = serializers.IntegerField()
    n_likes = serializers.IntegerField()
    n_dislikes = serializers.IntegerField()

    def get_cursor(self, obj):
        return getattr(obj, 'cursor', None)

    def get_is_played(self, obj):
        return getattr(obj, 'is_played', None)

    def get_is_liked(self, obj):
        return getattr(obj, 'is_liked', False)

    def get_is_disliked(self, obj):
        return getattr(obj, 'is_disliked', False)


class VideoSerializer(SearchResultSerializer):
    related_name = 'video'
    object_serializer_class = VideoObjectSerializer
    highlight_fields = ['title', 'description']


class SearchSerializer(serializers.Serializer):
    videos = VideoSerializer(many=True)
    channels = ChannelSerializer(many=True)


class PlaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Play
        fields = ('uid', 'user', 'video', 'created')

    uid = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    def get_user(self, obj):
        return { 'uid': obj.user.uid }

    def get_video(self, obj):
        return { 'uid': obj.video.uid }


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ('uid', 'user', 'video', 'rating', 'created')

    uid = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    def get_user(self, obj):
        return { 'uid': obj.user.uid }

    def get_video(self, obj):
        return { 'uid': obj.video.uid }


class DislikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dislike
        fields = ('uid', 'user', 'video', 'rating', 'created')

    uid = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    def get_user(self, obj):
        return { 'uid': obj.user.uid }

    def get_video(self, obj):
        return { 'uid': obj.video.uid }


class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = (
            'uid', 'user', 'video', 'position', 'created',
        )

    uid = serializers.CharField(read_only=True)
    user = serializers.SerializerMethodField()
    video = serializers.SerializerMethodField()

    def get_user(self, obj):
        return { 'uid': obj.user.uid }

    def get_video(self, obj):
        return { 'uid': obj.video.uid }


class OAuth2ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAuth2Client
        fields = (
            'user', 'client_id', 'client_name', 'website_uri',
            'description', 'scope', 'created',
        )

    user = UserSerializer(fields=('uid', 'username',))


class OAuth2TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = OAuth2Token
        fields = (
            'uid', 'client', 'token_type', 'scope', 'revoked',
            'expires_in', 'created',
        )

    uid = serializers.CharField(read_only=True)
    client = OAuth2ClientSerializer()


class OAuth2AuthzCodeSerializer(serializers.Serializer):
    client = OAuth2ClientSerializer()
