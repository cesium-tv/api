from django.urls import path

from rest_framework import routers

from rest.views import (
    render_brand_template, redirect_favicon, PublisherViewSet, UserViewSet,
    ChannelViewSet, VideoViewSet, OAuth2TokenViewSet, OAuthAuthorizationView,
    OAuthTokenView,
)


router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'tokens', OAuth2TokenViewSet, basename='token')

urlpatterns = [
    path('brand/theme.css', render_brand_template('theme.css')),
    path('brand/theme.js', render_brand_template('theme.js')),
    path('brand/favicon.ico', redirect_favicon),
    path(
        r'oauth2/authorize/',
        OAuthAuthorizationView.as_view(),
        name='oauth_authorize_view'
    ),
    path(
        r'oauth2/token/',
        OAuthTokenView.as_view(),
        name='oauth_token_view'
    ),
] + router.urls
