from django.contrib import admin
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
    UserChangeForm as BaseUserChangeForm
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from rest.models import User, Platform, Channel, Video, VideoSource


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


@admin.register(Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ('name', "url", )
    inlines = (ChannelInline, )


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "url")
    list_filter = ('platform', )


class VideoSourceInline(admin.TabularInline):
    model = VideoSource


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "platform", "channel", "poster", "published")
    list_filter = ("channel", )
    inlines = (VideoSourceInline, )


@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ("dimension", "video", "url")
    list_filter = ("video__channel", )
