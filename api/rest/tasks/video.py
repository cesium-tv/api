import os
import logging
from pprint import pprint
from itertools import repeat

from api.celery import task
from django.conf import settings

from rest.models import Publisher, Channel, Video, Tag, VideoSource
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
def import_channel(channel_id, depth=SENTINAL, limit=SENTINAL):
    options, channel = {}, Channel.objects.get(pk=channel_id)

    if channel.options:
        options.update(channel.options)
    if channel.publisher.options:
        options.update(channel.publisher.options)
    if depth is not SENTINAL:
        options['depth'] = depth
    if limit is not SENTINAL:
        options['limit'] = limit

    LOGGER.info('Importing channel')
    LOGGER.info('name: %s', channel.name)
    LOGGER.info('extern_id: %s', channel.extern_id)
    LOGGER.info('extern_cursor: %s', channel.extern_cursor)
    LOGGER.info('url: %s', channel.url)
    LOGGER.info('options: %s', options)

    _get_variable(options, 'credentials', 'username')
    _get_variable(options, 'credentials', 'password')

    objects = channel.platform.CrawlerClass(
        channel,
        options,
    ).crawl(channel.extern_cursor)

    for obj, state in objects:
        LOGGER.info('Saving video %s in channel %s', obj.extern_id, channel.name)
        video, created = Video.objects.get_or_create(
            channel=channel,
            extern_id=obj.extern_id,
            defaults={
                'title': obj.title,
                'poster': obj.poster,
                'duration': obj.duration,
                'original': obj.original,
                'published': obj.published,
            }
        )
        LOGGER.info('Adding tags %s to video', obj.tags)
        video.tags.set([
            Tag.objects.get_or_create(name=t)[0] for t in obj.tags
        ])
        for source in obj.sources:
            LOGGER.info('Adding source %s to video', source.url)
            VideoSource.objects.get_or_create(
                video=video,
                url=source.url,
                width=source.width,
                defaults={
                    'height': source.height,
                    'fps': source.fps,
                    'size': source.size,
                    'original': source.original,
                }
            )

        LOGGER.info('Updating channel state to %s', state)
        channel.update(extern_cursor=state)


@task
def import_videos():
    for channel in Channel.objects.all():
        import_channel.delay(channel.id)
