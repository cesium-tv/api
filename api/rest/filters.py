import django_filters as filters
from django_filters.constants import EMPTY_VALUES

from django.contrib.postgres.search import SearchQuery
from django.db.models import Count, Func

from rest.models import User, Video, Channel, Package, Tag


class SearchFilter(filters.CharFilter):
    # NOTE: performs full-text search.
    # TODO: ranking excerpts etc.
    def filter(self, queryset, value):
        if value in EMPTY_VALUES:
            return queryset
        return queryset.filter(search=SearchQuery(value))


class CICharFilter(filters.CharFilter):
    # Searches with collation compatible with CI fields.
    def filter(self, queryset, value):
        if value in EMPTY_VALUES:
            return queryset
        value_ci = Func(
            self.field_name,
            function='tr-TR-x-icu',
            template='(%(expressions)s) COLLATE "%(function)s"',
        )
        annotated = '%s_ci' % self.field_name
        lookup = '%s__%s' % (annotated, self.lookup_expr)
        return queryset \
            .annotate(**{annotated: value_ci}) \
            .filter(**{lookup: value})


class UserFilterSet(filters.FilterSet):
    class Meta:
        model = User
        fields = {
            'username': ['exact', 'startswith', 'contains', 'icontains'],
        }

    order = filters.OrderingFilter(
        fields=(
            ('username', 'username'),
        ),
    )


class VideoFilterSet(filters.FilterSet):
    class Meta:
        model = Video
        fields = {
            'duration': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'published': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }

    order = filters.OrderingFilter(
        fields=(
            ('n_plays', 'n_plays'),
            ('n_likes', 'n_likes'),
            ('n_dislikes', 'n_dislikes'),
        ),
    )

    search = SearchFilter(field_name='search')
    tags__name = filters.CharFilter(
        field_name='tags__name', lookup_expr='exact')
    tags__name__startswith = CICharFilter(
        field_name='tags__name', lookup_expr='startswith')
    tags__name__contains = CICharFilter(
        field_name='tags__name', lookup_expr='contains')
    n_plays = filters.NumberFilter(field_name='n_plays', lookup_expr='exact')
    n_plays__gt = filters.NumberFilter(field_name='n_plays', lookup_expr='gt')
    n_plays__gte = filters.NumberFilter(
        field_name='n_plays', lookup_expr='gte')
    n_plays__lt = filters.NumberFilter(field_name='n_plays', lookup_expr='lt')
    n_plays__lte = filters.NumberFilter(
        field_name='n_plays', lookup_expr='lte')
    n_likes = filters.NumberFilter(field_name='n_likes', lookup_expr='exact')
    n_likes__gt = filters.NumberFilter(field_name='n_likes', lookup_expr='gt')
    n_likes__gte = filters.NumberFilter(
        field_name='n_likes', lookup_expr='gte')
    n_likes__lt = filters.NumberFilter(field_name='n_likes', lookup_expr='lt')
    n_likes__lte = filters.NumberFilter(
        field_name='n_likes', lookup_expr='lte')
    n_dislikes = filters.NumberFilter(
        field_name='n_dislikes', lookup_expr='exact')
    n_dislikes__gt = filters.NumberFilter(
        field_name='n_dislikes', lookup_expr='gt')
    n_dislikes__gte = filters.NumberFilter(
        field_name='n_dislikes', lookup_expr='gte')
    n_dislikes__lt = filters.NumberFilter(
        field_name='n_dislikes', lookup_expr='lt')
    n_dislikes__lte = filters.NumberFilter(
        field_name='n_dislikes', lookup_expr='lte')


class ChannelFilterSet(filters.FilterSet):
    class Meta:
        model = Channel
        fields = {
            'name': ['exact', 'startswith', 'contains', 'icontains'],
            'title': ['exact', 'startswith', 'contains', 'icontains'],
            'description': ['exact', 'startswith', 'contains', 'icontains'],
            'url': ['exact', 'startswith', 'contains', 'icontains'],
        }

    order = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('n_videos', 'n_videos'),
        ),
    )

    search = SearchFilter(field_name='search')
    n_videos = filters.NumberFilter(field_name='n_videos', lookup_expr='exact')
    n_videos__gt = filters.NumberFilter(field_name='n_videos', lookup_expr='gt')
    n_videos__gte = filters.NumberFilter(
        field_name='n_videos', lookup_expr='gte')
    n_videos__lt = filters.NumberFilter(field_name='n_videos', lookup_expr='lt')
    n_videos__lte = filters.NumberFilter(
        field_name='n_videos', lookup_expr='lte')


class PackageFilterSet(filters.FilterSet):
    class Meta:
        model = Package
        fields = {
            'name': ['exact', 'startswith', 'contains', 'icontains'],
            'price_ppv': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'price_month': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'price_year': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'price_lifetime': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }

    order = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('price_ppv', 'price_ppv'),
            ('price_month', 'price_month'),
            ('price_year', 'price_year'),
            ('price_lifetime', 'price_lifetime'),
        ),
    )


class TagFilterSet(filters.FilterSet):
    class Meta:
        model = Tag
        fields = {
            'name': ['exact', 'startswith', 'contains', 'icontains'],
        }

    order = filters.OrderingFilter(
        fields=(
            ('name', 'name'),
            ('n_tagged', 'n_tagged'),
        ),
    )

    # Filter by annotated column
    n_tagged = filters.NumberFilter(field_name='n_tagged', lookup_expr='exact')
    n_tagged__gt = filters.NumberFilter(
        field_name='n_tagged', lookup_expr='gt')
    n_tagged__gte = filters.NumberFilter(
        field_name='n_tagged', lookup_expr='gte')
    n_tagged__lt = filters.NumberFilter(
        field_name='n_tagged', lookup_expr='lt')
    n_tagged__lte = filters.NumberFilter(
        field_name='n_tagged', lookup_expr='lte')
