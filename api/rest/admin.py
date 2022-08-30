from django.db.models import Count
from django.contrib import admin
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
    UserChangeForm as BaseUserChangeForm
)
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin as BaseSiteAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from rest.models import (
    User, Publisher, Channel, Video, VideoSource, Tag, Subscription,
    SiteOption, Brand, OAuth2Client,
)


def reregister(*models, site=None):
    from django.contrib.admin import ModelAdmin
    from django.contrib.admin.sites import AdminSite
    from django.contrib.admin.sites import site as default_site

    def _model_admin_wrapper(admin_class):
        if not models:
            raise ValueError("At least one model must be passed to register.")

        admin_site = site or default_site

        if not isinstance(admin_site, AdminSite):
            raise ValueError("site must subclass AdminSite")

        if not issubclass(admin_class, ModelAdmin):
            raise ValueError("Wrapped class must subclass ModelAdmin.")

        for model in models:
            if admin_site.is_registered(model):
                admin_site.unregister(model)
        admin_site.register(models, admin_class=admin_class)

        return admin_class

    return _model_admin_wrapper


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = ('email',)


class SubscriptionInline(admin.TabularInline):
    model = Subscription


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('site',) + BaseUserAdmin.list_display
    fieldsets = (
        (None, {"fields": ("site", "username", "password")}),
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
    inlines = (SubscriptionInline, )


class SiteOptionInline(admin.StackedInline):
    model = SiteOption


@reregister(Site)
class SiteAdmin(BaseSiteAdmin):
    inlines = (SiteOptionInline, )


class ChannelInline(admin.TabularInline):
    model = Channel


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    list_display = ('name', "channel_count", )
    inlines = (ChannelInline, )

    def channel_count(self, obj):
        return obj.channel_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(channel_count=Count("channels"))
        return queryset


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "video_count", "subscriber_count", "url")
    list_filter = ('publisher', )
    inlines = (SubscriptionInline, )

    def video_count(self, obj):
        return obj.video_count

    def subscriber_count(self, obj):
        return obj.subscriber_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            video_count=Count("videos"),
            subscriber_count=Count("subscribers")
        )
        return queryset


class VideoSourceInline(admin.TabularInline):
    model = VideoSource


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "source_count", "channel", "poster", "published")
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


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    pass


@admin.register(OAuth2Client)
class OAuth2ClientAdmin(admin.ModelAdmin):
    list_display = ("user", "client_id", "client_name", "website_uri")
