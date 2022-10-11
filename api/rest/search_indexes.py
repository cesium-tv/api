import datetime
from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from rest.models import Video, Channel


class ChannelIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)

    def get_model(self):
        return Channel

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_text(self, object):
        return f'{object.name}\n{object.url}'


class VideoIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)
    tags = indexes.CharField()

    def get_model(self):
        return Video

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_text(self, object):
        return object.title

    def prepare_tags(self, object):
        return ' '.join([t.name for t in object.tags.all()])
