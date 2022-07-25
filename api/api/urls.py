from django.urls import path, include
from django.contrib import admin
from django.conf import settings


urlpatterns = [
    path('api/v1/', include('rest.urls.v1')),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
