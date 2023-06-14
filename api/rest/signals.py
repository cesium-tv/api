import logging
from collections import Counter

import spacy

from django.db.models.signals import post_save, m2m_changed, pre_delete
from django.dispatch import receiver
from django.db.models import Value
from django.contrib.postgres.search import SearchVector

from rest.models import Video, Channel, Tag, Term


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())

NLP = spacy.load('en_core_web_sm')


def extract_ngrams(instance, field_names):
    for field_name in field_names:
        text = getattr(instance, field_name)
        if text is None:
            continue
        for ngram in NLP(text).noun_chunks:
            yield ngram.text


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
    LOGGER.debug('Updating search terms for video id: %i', instance.id)
    ngrams = Counter(
        extract_ngrams(instance, ('title', 'description'))
    )
    Term.objects.bulk_create(ngrams.items())


@receiver(post_save, sender=Channel)
def update_channel_search(sender, instance, created, **kwargs):
    LOGGER.debug('Updating search terms for channel id: %i', instance.id)
    ngrams = Counter(
        extract_ngrams(instance, ('name', 'title', 'description', 'url'))
    )
    Term.objects.bulk_create(ngrams.items())
