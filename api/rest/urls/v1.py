from django.urls import path

from rest_framework import routers

from rest.views import (
    theme_js, theme_css, favicon, UserViewSet, ChannelViewSet, TagViewSet,
    VideoViewSet, OAuth2TokenViewSet, OAuthAuthCodeView, OAuthTokenView,
    OAuthDeviceCodeView, OAuthDeviceCodeVerifyView, SearchView,
)


router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'tokens', OAuth2TokenViewSet, basename='token')

urlpatterns = [
    path('brand/theme.css', theme_css),
    path('brand/theme.js', theme_js),
    path('brand/favicon.ico', favicon),
    path(
        'oauth2/device/verify/',
        OAuthDeviceCodeVerifyView.as_view(),
        name='oauth_device_code_verify_view'
    ),
    path(
        r'oauth2/authorize/',
        OAuthAuthCodeView.as_view(),
        name='oauth_auth_code_view'
    ),
    path(
        r'oauth2/device/',
        OAuthDeviceCodeView.as_view(),
        name='oauth_device_code_view'
    ),
    path(
        r'oauth2/token/',
        OAuthTokenView.as_view(),
        name='oauth_token_view'
    ),
    path(
        r'search/',
        SearchView.as_view(),
        name='search_view',
    ),
] + router.urls
