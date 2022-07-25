import shlex
import subprocess

from django.core.management.base import BaseCommand
from django.utils import autoreload
from django.conf import settings

CELERY_KILL = ('pkill', '-9', settings.CELERY_COMMAND[0])


def restart_celery(*args, **kwargs):
    subprocess.call(CELERY_KILL)
    subprocess.call(settings.CELERY_COMMAND)


class Command(BaseCommand):
    def handle(self, *args, **options):
        if settings.CELERY_AUTORELOAD:
            self.stdout.write('Starting celery worker with autoreload...')
            autoreload.run_with_reloader(restart_celery, args=None, kwargs=None)

        else:
            self.stdout.write('Starting celery worker...')
            subprocess.call(settings.CELERY_COMMAND)
