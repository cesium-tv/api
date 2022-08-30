import re
import itertools
import hmac
import socket
import json
import glob
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.http import HttpResponseRedirect, Http404
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.db.models import ObjectDoesNotExist
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.shortcuts import get_object_or_404, render, redirect
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
    UserSerializer, PublisherSerializer, ChannelSerializer, VideoSerializer,
    OAuth2AuthzCodeSerializer, OAuth2TokenSerializer,
)
from rest.models import (
    Publisher, Video, Channel, UserPlay, UserLike, SiteOption, Brand,
    OAuth2Token,
)


User = get_user_model()


def redirect_favicon(request):
    try:
        brand = SiteOption.objects.get(site=request.site).brand

    except ObjectDoesNotExist:
        raise Http404()

    return redirect(brand.favicon.url)


def render_brand_template(template_name):
    if template_name.endswith('.css'):
        content_type = 'text/css'
    elif template_name.endswith('.js'):
        content_type = 'text/javascript'
    elif template_name.endswith('.json'):
        content_type = 'application/json'
    else:
        content_type = 'text/html'

    def inner(request):
        try:
            options = SiteOption.objects.get(site=request.site)
            context = {
                'user': request.user,
                'site': request.site,
                'options': options,
                'brand': options.brand,
            }

        except ObjectDoesNotExist:
            raise Http404()

        return render(
            request, template_name, context=context, content_type=content_type
        )

    return inner


class UserViewSet(ModelViewSet):
    permission_classes = [CreateOrIsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = self.queryset \
            .filter(pk=self.request.user.id) \
            .filter(publisher__sites__in=[self.request.site])
        return queryset

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


class PublisherViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PublisherSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Publisher.objects \
            .annotate(
                num_channels=Count('channels'),
            ) \
            .filter(sites__in=[self.request.site])
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
            .filter(publisher__sites__in=[self.request.site])
        return queryset


class VideoViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = VideoSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Video.objects \
            .prefetch_related('sources') \
            .order_by('-published') \
            .filter(channel__publisher__sites__in=[self.request.site])

        user_id = getattr(self.request.user, 'id', None)
        if user_id:
            queryset = queryset.annotate(
                played=Exists(
                    UserPlay.objects.filter(
                        video_id=OuterRef('pk'),
                        user_id=user_id)
                ),
                liked=Exists(
                    UserLike.objects.filter(
                        video_id=OuterRef('pk'),
                        user_id=user_id,
                        like=1)
                ),
                disliked=Exists(
                    UserLike.objects.filter(
                        video_id=OuterRef('pk'),
                        user_id=user_id,
                        like=-1)
                ),
            )

        channel_uid = self.request.query_params.get('channel')
        if channel_uid is not None:
            channel = get_object_or_404(Channel,
                publisher__sites__in=[self.request.site],
                uid=channel_uid,
            )
            queryset = queryset.filter(channel=channel)

        return queryset


class OAuthAuthorizationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        grant = SERVER.get_consent_grant(request, end_user=request.user)
        serializer = OAuth2AuthzCodeSerializer(grant)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        is_confirmed = request.data.get('confirm') == 'true'
        user = request.user if is_confirmed else None
        # NOTE: returns a redirect, no serialization necessary.
        return SERVER.create_authorization_response(request, grant_user=user)


class OAuthTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return SERVER.create_token_response(request)


class OAuth2TokenViewSet(DestroyModelMixin, ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OAuth2TokenSerializer
    queryset = OAuth2Token.objects.all()
    lookup_field = 'uid'

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
