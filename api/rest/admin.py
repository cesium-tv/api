from django.db.models import Count
from django.contrib import admin
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
    UserChangeForm as BaseUserChangeForm
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from rest.models import User, Publisher, Channel, Video, VideoSource


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = ('email',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "is_confirmed")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )


class ChannelInline(admin.TabularInline):
    model = Channel


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', "channel_count", "url", )
    inlines = (ChannelInline, )

    def channel_count(self, obj):
        return obj.channel_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(channel_count=Count("channels"))
        return queryset


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "video_count", "url")
    list_filter = ('publisher', )

    def video_count(self, obj):
        return obj.video_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(video_count=Count("videos"))
        return queryset


class VideoSourceInline(admin.TabularInline):
    model = VideoSource


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "source_count", "publisher", "channel", "poster", "published")
    list_filter = ("channel", )
    inlines = (VideoSourceInline, )
    ordering = ('-published',)

    def source_count(self, obj):
        return obj.source_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(source_count=Count("sources"))
        return queryset


@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ("dimension", "video", "url")
    list_filter = ("video__channel", )
