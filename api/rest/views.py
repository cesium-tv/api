import re
import itertools
import hmac
import socket
import json
import glob
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.http import HttpResponseRedirect
from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Exists, Count, OuterRef
from django.utils import timezone

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.mixins import DestroyModelMixin
from rest_framework.generics import CreateAPIView, RetrieveAPIView
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import (
    IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated,
)

from rest.permissions import CreateOrIsAuthenticated
from rest.serializers import (
    UserSerializer, PlatformSerializer, ChannelSerializer, VideoSerializer,
)
from rest.models import (
    Platform, Video, Channel, UserVideo, UserLike, UserDislike,
)


User = get_user_model()


class UserViewSet(ModelViewSet):
    permission_classes = [CreateOrIsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'uid'

    def get_queryset(self):
        return self.queryset.filter(pk=self.request.user.id)

    def perform_create(self, serializer):
        user = serializer.save()
        user.send_confirmation_email(self.request)

    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def login(self, request):
        email = request.data['email']
        password = request.data['password']
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response('', status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def logout(self, request):
        logout(request)
        return Response('', status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'], permission_classes=[AllowAny])
    def whoami(self, request):
        user = get_object_or_404(User, pk=request.user.id)
        serializer = self.serializer_class(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], permission_classes=[AllowAny])
    def confirm(self, request, uid=None):
        next = request.query_params.get('next', '/#/login')
        serializer = UserConfirmSerializer(uid, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return HttpResponseRedirect(next)


class PlatformViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PlatformSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Platform.objects \
            .annotate(
                num_channels=Count('channels'),
            ) \
            .all()

        return queryset


class ChannelViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChannelSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Channel.objects \
            .annotate(
                num_videos=Count('videos'),
                num_subscribers=Count('subscribers'),
            ) \
            .all()
        return queryset

class VideoViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = VideoSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Video.objects \
            .prefetch_related('sources') \
            .order_by('-published') \
            .annotate(
                num_plays=Count('plays'),
                num_likes=Count('likes'),
                num_dislikes=Count('dislikes'),
                # played=Exists(UserVideo.objects.filter(video_id=OuterRef('pk'), user=self.request.user)),
                # liked=Exists(UserLike.objects.filter(video_id=OuterRef('pk'), user=self.request.user)),
                # disliked=Exists(UserDislike.objects.filter(video_id=OuterRef('pk'), user=self.request.user)),
                played=Exists(UserVideo.objects.filter(video_id=OuterRef('pk'), user_id=1)),
                liked=Exists(UserLike.objects.filter(video_id=OuterRef('pk'), user_id=1)),
                disliked=Exists(UserDislike.objects.filter(video_id=OuterRef('pk'), user_id=1)),
            ) \
            .all()
        channel_id = self.request.query_params.get('channel')
        if channel_id is not None:
            channel = get_object_or_404(Channel, uid=channel_id)
            queryset = queryset.filter(channel=channel)
        return queryset
