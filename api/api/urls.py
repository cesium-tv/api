from django.urls import path, include
from django.contrib import admin
from django.conf import settings

from rest.views import OAuthDeviceCodeVerifyView

urlpatterns = [
    path('api/v1/', include('rest.urls.v1')),
    path('admin/', admin.site.urls),
    path(
        'verify/',
        OAuthDeviceCodeVerifyView.as_view(),
        name='oauth_device_code_verify_view'
    ),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
