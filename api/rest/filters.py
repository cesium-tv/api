import rest_framework_filters as filters

from rest.models import Video


class VideoFilter(filters.FilterSet):
    class Meta:
        model = Video
        fields = ('duration',)
