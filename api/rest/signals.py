from django.db.models.signals import post_save, m2m_changed
from django.dispatch import receiver
from django.db.models import Func, F
from django.contrib.postgres.search import SearchVector


@receiver(post_save, sender='rest.Video')
def update_video_search(sender, instance, created, **kwargs):
    sender.objects \
        .filter(id=instance.id) \
        .update(search=SearchVector('title', 'description', 'tags'))


@receiver(post_save, sender='rest.Channel')
def update_video_search(sender, instance, created, **kwargs):
    sender.objects \
        .filter(id=instance.id) \
        .update(search=SearchVector('name', 'title', 'description', 'url'))
