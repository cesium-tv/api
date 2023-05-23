import re
import itertools
import hmac
import socket
import json
import glob
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.cache import cache
from django.contrib.sites.models import Site
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth import get_user_model, login, logout, authenticate
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db import transaction
from django.db.models import Exists, Count, OuterRef, Subquery, Func, F
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
    UserSerializer, ChannelSerializer, VideoSerializer, OAuth2ClientSerializer,
    OAuth2TokenSerializer, PlaySerializer, LikeSerializer, DislikeSerializer,
)
from rest.models import (
    Video, Channel, Play, Like, Dislike, SiteOption, Brand, OAuth2Token,
    OAuth2DeviceCode, OAuth2Client, Subscription,
)
from rest.oauth import SERVER


User = get_user_model()


def favicon(request):
    try:
        brand = SiteOption.objects.get(site=request.site).brand

    except SiteOption.DoesNotExist:
        raise Http404()

    return redirect(brand.favicon.url)


def theme_css(request):
    try:
        brand = SiteOption.objects.get(site=request.site).brand

    except SiteOption.DoesNotExist:
        raise Http404()

    try:
        css = brand.theme_css.read()

    except FileNotFoundError:
        raise Http404()

    return HttpResponse(css, content_type='text/css')


def theme_js(request):
    try:
        options = SiteOption.objects.get(site=request.site)
        context = {
            'user': request.user,
            'site': request.site,
            'options': options,
            'menu_items': options.menu_items.all().order_by('sort', 'id'),
            'brand': options.brand,
        }

    except SiteOption.DoesNotExist:
        raise Http404()

    return render(
        request, 'theme.js', context=context, content_type='text/javascript'
    )


class UserViewSet(ModelViewSet):
    permission_classes = [CreateOrIsAuthenticated]
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = self.queryset \
            .filter(pk=self.request.user.id) #\
            #.filter(publisher__sites__in=[self.request.site])
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()
        user.send_confirmation_email(self.request)

    @action(detail=False, methods=['POST'], permission_classes=[AllowAny])
    def login(self, request):
        try:
            username = request.data['username']
            password = request.data['password']

        except KeyError as e:
            return Response(
                {'missing': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
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


class ChannelViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ChannelSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Channel.objects.all()

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(public=True)

        else:
            # NOTE: we select all channels that relate to a package that the
            # user subscribes to.        
            subbed = Subscription.objects.filter(
                package__channels__id=OuterRef('id'),
                user=self.request.user
            )

            queryset = queryset.filter(Exists(subbed))
        return queryset


class VideoViewSet(ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = VideoSerializer
    lookup_field = 'uid'

    def get_queryset(self):
        queryset = Video.objects \
            .prefetch_related('sources') \
            .order_by('-published')

        if not self.request.user.is_authenticated:
            queryset = queryset.filter(channel__public=True)

        else:
            subbed = Subscription.objects.filter(
                package__channels__id=OuterRef('channel_id'),
                user=self.request.user
            )

            queryset = queryset.annotate(
                played=Exists(
                    Play.objects.filter(
                        video_id=OuterRef('pk'),
                        user=self.request.user)
                ),
                liked=Exists(
                    Like.objects.filter(
                        video_id=OuterRef('pk'),
                        user=self.request.user)
                ),
                disliked=Exists(
                    Dislike.objects.filter(
                        video_id=OuterRef('pk'),
                        user=self.request.user)
                ),
            ).filter(Exists(subbed))

        channel_uid = self.request.query_params.get('channel')
        if channel_uid is not None:
            channel = get_object_or_404(Channel,
                publisher__sites__in=[self.request.site],
                uid=channel_uid,
            )
            queryset = queryset.filter(channel=channel)

        return queryset

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def like(self, request, uid):
        like, created = Like.objects.get_or_create(
            user=request.user, video=video)
        serializer = LikeSerializer(like, many=False)
        status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def dislike(self, request, uid):
        dislike, created = Dislike.objects.get_or_create(
            user=request.user, video=video)
        serializer = DislikeSerializer(dislike, many=False)
        status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status)

    @action(detail=True, methods=['POST'], permission_classes=[IsAuthenticated])
    def played(self, request, uid):
        play, created = Play.objects.get_or_create(
            user=request.user, video=video)
        serializer = PlaySerializer(play, many=False)
        status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status)


class OAuthAuthCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # This view returns serialized data that is used by vuejs UI to ask
        # the user to approve access to their account.
        grant = SERVER.get_consent_grant(request, end_user=request.user)
        serializer = OAuth2ClientSerializer(grant['client'])
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Handle the user confirming or denying access. The user is redirected
        # back to the requesting application, where they will display an error
        # or fetch a token from the token endpoint.
        is_confirmed = request.data.get('confirm') == 'true'
        user = request.user if is_confirmed else None
        # NOTE: returns a redirect, no serialization necessary.
        return SERVER.create_authorization_response(request, grant_user=user)


class OAuthDeviceCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        return SERVER.create_endpoint_response('device_authorization', request)


class OAuthDeviceCodeVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # This view should explain to the user that entering the code
        # and approving the request will result in the TV having access
        # to their account.
        try:
            user_code = request.query_params['user_code']
        except KeyError as e:
            return Response(
                {'missing': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        client = get_object_or_404(OAuth2Client, device_codes__user_code=user_code)
        serializer = OAuth2ClientSerializer(client)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        # Handle the user confirming or denying access. The polling device will
        # receive the result of this operation on it's next poll.
        try:
            user_code=request.query_params['user_code']

        except KeyError as e:
            return Response(
                {'missing': e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        allowed = request.data.get('confirm') in (True, 'true')
        code = get_object_or_404(OAuth2DeviceCode, user_code=user_code)
        code.user = request.user
        code.allowed = allowed
        code.save()
        if allowed:
            response = Response({'message': 'OK'}, status=status.HTTP_200_OK)
        else:
            response = Response(
                {'message': 'must check confirm'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return response


class OAuthTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # import pdb; pdb.set_trace()
        return SERVER.create_token_response(request)


class OAuth2TokenViewSet(DestroyModelMixin, ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = OAuth2TokenSerializer
    queryset = OAuth2Token.objects.all()
    lookup_field = 'uid'

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
