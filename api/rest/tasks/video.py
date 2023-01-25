import os
import asyncio
import logging
import time

from pprint import pprint
from itertools import repeat
from dataclasses import asdict

from celery import chain
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import IntegrityError
from videosrc import crawl_sync  # , auth_sync
# from videosrc.errors import AuthenticationFailure

from api.celery import task
from rest.models import (
    Subscription, Channel, Video, VideoMeta, Tag, VideoSource,
    VideoSourceMeta, SubscriptionVideo,
)


LOGGER = get_task_logger(__name__)


@task(bind=True, max_retries=3)
def crawl_subscription(self, subscription_id):
    state = None
    subscription = Subscription.objects.get(pk=subscription_id)
    channel, videos = crawl_sync(
        subscription.channel.url,
        state=subscription.crawl_state,
        credentials=subscription.auth_info
    )

    try:
        for vinfo, state in videos:
            defaults = asdict(vinfo)
            tags = defaults.pop('tags')
            sources = defaults.pop('sources')
            original = defaults.pop('original')
            video, _ = Video.objects.update_or_create(
                extern_id=vinfo.extern_id,
                channel=subscription.channel,
                defaults=defaults)
            SubscriptionVideo.objects.get_or_create(
                video=video, subscription=subscription)
            VideoMeta.objects.update_or_create(
                video=video, defaults={'metadata': original})
            for tag in tags:
                video.tags.add(Tag.objects.get_or_create(name=tag)[0])
            for sinfo in sources:
                original = sinfo.pop('original')
                video_source, _ = VideoSource.objects.update_or_create(
                    extern_id=sinfo['extern_id'],
                    video=video,
                    defaults=sinfo,
                )
                VideoSourceMeta.objects.update_or_create(
                    source=video_source,
                    defaults={'metadata': original})

            subscription.crawl_state = state
            subscription.save()

    except Exception as e:
        LOGGER.exception(e)
        self.retry(exc=e)


@task
def clone_subscription(subscription_id):
    subscription = Subscription.objects.get(pk=subscription_id)
    try:
        login_sync(subscription.channel.url, **subscription.auth_info)

    except AuthenticationFailure as e:
        LOGGER.exception(e)
        return

    for video in subscription.channel.videos:
        try:
            SubscriptionVideo.objects.create(
                subscription=subscription, video=video)

        except IntgrityError:
            LOGGER.debug('Video %i already ')
            continue


@task
def update_channel(channel_id):
    channel = Channel.objects.get(channel_id)
    task = chain()
    if channel.options.universal:
        # Update owner subscription to fetch latest videos.
        owner_id = Subscription.objects \
            .get(channel=channel, user=channel.user) \
            .values_list('pk', flat=True)[0]
        task |= crawl_subscription.si(owner_id)

        # Check auth info for all subscriptions and copy videos.
        for subscription_id in Subscription.objects \
            .filter(channel=channel) \
            .exclude(user=channel.user) \
            .values_list('pk', flag=True):
            task |= clone_subscription.si(subscription_id)

    else:
        # Update all subscriptions using their unique auth.
        for subscription_id in Subscription.objects \
            .filter(channel=channel) \
            .values_list('pk', flat=True):
            task |= crawl_subscription.si(subscription_id)

    task.delay()
