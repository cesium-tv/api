import os
import logging
from pprint import pprint
from itertools import repeat

from api.celery import task
from django.conf import settings

from rest.models import Platform, Channel, Video, VideoSource
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
def save_video(channel_id, json):
    channel = Channel.objects.get(pk=channel_id)

    try:
        video = Video.objects.from_json(channel, json)
        LOGGER.info('Imported video id: %i', video.id)

    except:
        LOGGER.exception('Import failed')


@task
def import_channel(channel_id, depth=SENTINAL, limit=SENTINAL):
    channel = Channel.objects.get(pk=channel_id)

    options = channel.options.copy()
    options.update(channel.platform.options)
    if depth is not SENTINAL:
        options['depth'] = depth
    if limit is not SENTINAL:
        options['limit'] = limit

    LOGGER.info('channel.name: %s', channel.name)
    LOGGER.info('channel.url: %s', channel.url)
    LOGGER.info('options: %s', options)

    _get_variable(options, 'login', 'username', 1)
    _get_variable(options, 'login', 'password', 1)

    videos = vidsrc.download(
        channel.name,
        channel.url,
        options,
    )
    for video in videos:
        save_video.delay(channel_id, video)


@task
def import_videos():
    for channel in Channel.objects.all():
        import_channel.delay(channel.id)
