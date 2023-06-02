import os
import types
from celery import Celery
from celery.signals import worker_ready


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

app = Celery('api')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# @worker_ready.connect
# def at_start(sender, **k):
#     with sender.app.connection() as conn:
#         sender.app.send_task('rest.tasks.video.import_videos', (1,))


def task(*args, **kwargs):
    return app.task(*args, **kwargs)
