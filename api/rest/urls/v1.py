from django.urls import path

from rest_framework import routers

from rest.views import (
    PublisherViewSet, UserViewSet, ChannelViewSet, VideoViewSet,
)


router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'publishers', PublisherViewSet, basename='publisher')

urlpatterns = [
] + router.urls