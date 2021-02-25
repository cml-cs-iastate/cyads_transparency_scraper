from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.django import DjangoIntegration


sentry_sdk.init("https://75842aa0063e42edb61fcfd410c9bd23@sentry.io/2564250", integrations=[CeleryIntegration(),
                                                                                            DjangoIntegration()],
                )

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cyads_transparency_web.settings')

app = Celery('cyads_transparency_web')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.broker_url = 'redis://localhost:6379/0'


# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
