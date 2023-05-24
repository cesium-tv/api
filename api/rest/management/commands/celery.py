import shlex
import subprocess
import logging

from functools import partial

from django.core.management.base import BaseCommand
from django.utils import autoreload
from django.conf import settings


CELERY_KILL = ('pkill', '-9', settings.CELERY_COMMAND[0])
LOGGER = logging.getLogger(__name__)


def restart_celery(celery_command, **kwargs):
    subprocess.call(CELERY_KILL)
    subprocess.call(celery_command)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--uid', type=int)
        parser.add_argument('--gid', type=int)

    def handle(self, *args, **options):
        LOGGER.debug('Celery args: %s', args)
        LOGGER.debug('Celery options: %s', options)

        celery_command = settings.CELERY_COMMAND

        if options['uid']:
            celery_command += ('--uid', str(options['uid']))
        if options['gid']:
            celery_command += ('--gid', str(options['gid']))

        if settings.CELERY_AUTORELOAD:
            LOGGER.info('Starting celery worker with autoreload...')
            autoreload.run_with_reloader(
                partial(restart_celery, celery_command))

        else:
            LOGGER.info('Starting celery worker...')
            subprocess.call(celery_command)
