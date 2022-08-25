from django.urls import path

from rest_framework import routers

from rest.views import (
    render_brand_template, PublisherViewSet, UserViewSet, ChannelViewSet,
    VideoViewSet,
)


router = routers.SimpleRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'publishers', PublisherViewSet, basename='publisher')

urlpatterns = [
    path('brand/theme.css', render_brand_template('theme.css')),
    path('brand/options.js', render_brand_template('options.js')),
] + router.urls
