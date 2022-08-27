import os
import logging
from pprint import pprint
from itertools import repeat

from api.celery import task
from django.conf import settings

from rest.models import Publisher, Channel, Video, VideoSource
import vidsrc


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())
SENTINAL = object()


def _get_variable(d, *keys):
    final = keys[-1]
    for key in keys[:-1]:
        d = d[key]
    var_name = d[final]
    # Reads from env when: env[variable_name]
    if var_name.startswith('env[') and var_name.endswith(']'):
        d[final] = os.getenv(var_name[4:-1])
    # Reads from settings when: settings[variable_name]
    if var_name.startswith('settings[') and var_name.endswith(']'):
        d[final] = getattr(settings, var_name[9:-1])


@task
def import_channel(channel_id, url=None, depth=SENTINAL, limit=SENTINAL):
    channel = Channel.objects.get(pk=channel_id)

    options = channel.options.copy()
    options.update(channel.publisher.options)
    if depth is not SENTINAL:
        options['depth'] = depth
    if limit is not SENTINAL:
        options['limit'] = limit
    if url is None:
        url = channel.url

    LOGGER.info('channel.name: %s', channel.name)
    LOGGER.info('url: %s', url)
    LOGGER.info('options: %s', options)

    _get_variable(options, 'credentials', 'username', 1)
    _get_variable(options, 'credentials', 'password', 1)

    videos = channel.crawl_klass(url).crawl(
        url,
        options,
        state=channel.cursor,
        VideoModel=Video,
        VideoSourceModel=VideoSource,
    )

    for video, state in videos:
        video.save()
        channel.update(cursor=state)


@task
def import_videos():
    for channel in Channel.objects.all():
        import_channel.delay(channel.id)
