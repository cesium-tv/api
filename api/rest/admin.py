import ast

from django.db.models import Count
from django.contrib import admin
from django.contrib.auth.forms import (
    UserCreationForm as BaseUserCreationForm,
    UserChangeForm as BaseUserChangeForm
)
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin as BaseSiteAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin import widgets
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.urls import reverse

from bitfield import BitField
from bitfield.forms import BitFieldCheckboxSelectMultiple
from picklefield.fields import PickledObjectField, dbsafe_encode

from rest.models import (
    User, Channel, Video, VideoSource, Subscription, SiteOption,
    MenuItem, Brand, OAuth2Client, StripeAccount, Package,
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


class EditLinkToInlineObject(object):
    def advanced_options(self, instance):
        url = reverse('admin:%s_%s_change' % (
            instance._meta.app_label,  instance._meta.model_name),  args=[instance.pk] )
        if instance.pk:
            return mark_safe(u'<a href="{u}">show</a>'.format(u=url))
        else:
            return ''


class PickledObjectFieldTextAreaWidget(widgets.AdminTextareaWidget):
    def value_from_datadict(self, data, files, name):
        value = data.get(name)
        # we gotta have a PickledObject here otherwise CharField cleaning kicks in
        return dbsafe_encode(ast.literal_eval(value), False, 2, True)


class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('email',)


class UserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = ('email',)


class SubscriptionInline(admin.TabularInline):
    formfield_overrides = {
            BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }
    model = Subscription


class StripeAccountInline(admin.TabularInline):
    model = StripeAccount
    fields = ('account_id', )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = BaseUserAdmin.list_display + ('site',)
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
    inlines = (SubscriptionInline, StripeAccountInline, )


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', )
    formfield_overrides = {
            BitField: {'widget': BitFieldCheckboxSelectMultiple},
    }
    inlines = (SubscriptionInline, )


class PackageInline(admin.TabularInline):
    model = Package


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    ordering = ('sort', 'id', )


class SiteOptionInline(EditLinkToInlineObject, admin.StackedInline):
    model = SiteOption
    fields = (
        'title', 'brand', 'default_lang', 'auth_method', 'auth_required',
        'advanced_options',
    )
    readonly_fields = ('advanced_options', )


@admin.register(SiteOption)
class SiteOptionAdmin(admin.ModelAdmin):
    inlines = (MenuItemInline, )


@reregister(Site)
class SiteAdmin(BaseSiteAdmin):
    list_display = ('name', 'domain')
    inlines = (SiteOptionInline, )


class ChannelInline(admin.TabularInline):
    model = Channel


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = (
        "name", "user", "video_count", "url", 'created', 'updated',
    )
    formfield_overrides = {
            BitField: {'widget': BitFieldCheckboxSelectMultiple},
            PickledObjectField: {
                'widget': PickledObjectFieldTextAreaWidget,
            },
    }
    exclude = ('search',)

    def video_count(self, obj):
        return obj.video_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(
            video_count=Count("videos"),
        )
        return queryset


class VideoSourceInline(admin.TabularInline):
    model = VideoSource


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("title", "source_count", "poster", "published")
    list_filter = ("channel", )
    inlines = (VideoSourceInline, )
    ordering = ('-published',)
    readonly_fields = ('uid', )

    def source_count(self, obj):
        return obj.source_count

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(source_count=Count("sources"))
        return queryset


@admin.register(VideoSource)
class VideoSourceAdmin(admin.ModelAdmin):
    list_display = ("dimension", "video", "url", 'created', 'updated')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'scheme', 'created', 'updated')
    readonly_fields = ('theme_css', )


@admin.register(OAuth2Client)
class OAuth2ClientAdmin(admin.ModelAdmin):
    list_display = ("user", "client_id", "client_name", "website_uri")
