import logging

from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.db.models import Value
from django.contrib.postgres.search import SearchVector

from rest.models import Video, Channel, Tag


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


@receiver(pre_delete, sender=Tag)
def tag_delete_search(sender, instance, **kwargs):
    # NOTE: deleting a Tag does not send m2m_changed, only using the m2m
    # manager methods does. This code sends m2m_changed so we can update the
    # index. https://code.djangoproject.com/ticket/17688
    LOGGER.debug('Dispatching m2m_changed for tag deletion')
    for video in instance.tagged.all():
        m2m_changed.send(
            Video.tags.through, instance=video, action='pre_remove')


@receiver(post_save, sender=Video)
@receiver(m2m_changed, sender=Video.tags.through)
def update_video_search(sender, instance, **kwargs):
    LOGGER.debug('Updating search vectors for video id: %i', instance.id)
    #tags_str = ' '.join(instance.tags.all().values_list('name', flat=True))
    Video.objects \
        .filter(id=instance.id) \
        .update(search=SearchVector('title', 'description'))  #, Value(tags_str)))


@receiver(post_save, sender=Channel)
def update_video_search(sender, instance, created, **kwargs):
    LOGGER.debug('Updating search vectors for channel id: %i', instance.id)
    Channel.objects \
        .filter(id=instance.id) \
        .update(search=SearchVector('name', 'title', 'description', 'url'))
