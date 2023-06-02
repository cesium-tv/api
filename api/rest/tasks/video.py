import os
import asyncio
import logging
import time
import random

from pprint import pprint, pformat
from itertools import repeat

from celery import chain
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import IntegrityError, DatabaseError
from videosrc import crawl_sync

from api.celery import task
from rest.models import (
    Subscription, Channel, ChannelMeta, Video, VideoMeta, VideoSource,
    VideoSourceMeta,
)


LOGGER = get_task_logger(__name__)


def save_state_factory(channel):
    def save_state(state):
        LOGGER.info('Saving state for channel %s', channel.name)
        channel.update(state=state)
    return save_state


@task(bind=True, max_retries=3)
def update_channel(self, channel_id):
    try:
        channel = Channel.objects.get(pk=channel_id)
    except Channel.DoesNotExist:
        LOGGER.warning('Invalid channel id %i', channel_id)
        return

    try:
        auth_params = channel.auth_params or {}
        channel_data, videos = crawl_sync(
            channel.url,
            state=channel.state,
            save_state=save_state_factory(channel),
            **auth_params,
        )
        channel.from_dataclass(channel_data)

        for video in videos:
            video, created = Video.objects.from_dataclass(channel, video)
            if created:
                LOGGER.debug('Added new video %s', video.id)

            else:
                LOGGER.info('Updated video %s', video.id)

    except DatabaseError:
        LOGGER.exception('Error saving video data')
    
    except Exception as e:
        LOGGER.exception('Error fetching video data')
        self.retry(exc=e)


@task
def update_channels():
    # NOTE: we use a chain so updates run one after the other.
    tasks = chain()
    for channel in Channel.objects.all():
        LOGGER.debug('Scheduling channel update for %s', channel.name)
        tasks |= update_channel.si(channel.id)
    tasks.delay()
