import datetime
from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from rest.models import Video, Channel


class ChannelIndex(CelerySearchIndex, indexes.Indexable):
    uid = indexes.CharField()
    text = indexes.CharField(document=True)
    is_public = indexes.BooleanField()

    def get_model(self):
        return Channel

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_uid(self, object):
        return object.uid

    def prepare_text(self, object):
        return f'{object.name}\n{object.title}\n{object.description}\n{object.url}'
    
    def prepare_public(self, object):
        return object.is_public


class VideoIndex(CelerySearchIndex, indexes.Indexable):
    uid = indexes.CharField()
    text = indexes.CharField(document=True)
    tags = indexes.CharField()
    channel_uid = indexes.CharField()
    is_public = indexes.BooleanField()

    def get_model(self):
        return Video

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_uid(self, object):
        return object.uid

    def prepare_text(self, object):
        return f'{object.title}\n{object.description}'

    def prepare_tags(self, object):
        return ' '.join([t.name for t in object.tags.all()])

    def prepare_channel_uid(self, object):
        return object.channel.uid

    def prepare_is_public(self, object):
        return object.channel.is_public
