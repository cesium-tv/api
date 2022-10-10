import datetime
from haystack import indexes
from celery_haystack.indexes import CelerySearchIndex
from rest.models import Video, Channel


# publisher = models.ForeignKey(
#     Publisher, related_name='channels', on_delete=models.CASCADE)
# platform = models.ForeignKey(
#     Platform, related_name='channels', on_delete=models.CASCADE)
# name = models.CharField(max_length=64)
# url = models.URLField()
# extern_id = models.CharField(max_length=128, unique=True)
# extern_cursor = models.JSONField(null=True, blank=True)
# options = models.JSONField(null=True, blank=True)
# created = models.DateTimeField(auto_now_add=True)
# updated = models.DateTimeField(auto_now=True)
class ChannelIndex(CelerySearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True)

    def get_model(self):
        return Channel

    def index_queryset(self, using=None):
        return self.get_model().objects.all()

    def prepare_text(self, object):
        return f'{object.name}\n{object.url}''


# channel = models.ForeignKey(
#     Channel, related_name='videos', on_delete=models.CASCADE)
# tags = models.ManyToManyField(Tag, related_name='tagged')
# extern_id = models.CharField(max_length=128, unique=True)
# title = models.CharField(max_length=256)
# poster = models.URLField()
# duration = models.PositiveIntegerField()
# original = models.JSONField(null=True, blank=True)
# total_plays = models.PositiveIntegerField(default=0)
# total_likes = models.PositiveIntegerField(default=0)
# total_dislikes = models.PositiveIntegerField(default=0)
# published = models.DateTimeField(default=timezone.now)
# created = models.DateTimeField(auto_now_add=True)
# updated = models.DateTimeField(auto_now=True)
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
