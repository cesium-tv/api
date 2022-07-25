from django.urls import path

from rest_framework import routers

from rest.views import (
    PlatformViewSet, UserViewSet, ChannelViewSet, VideoViewSet,
)


router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'platforms', PlatformViewSet, basename='platform')

urlpatterns = [
] + router.urls