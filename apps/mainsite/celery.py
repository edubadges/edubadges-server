# Created by wiggins@concentricsky.com on 8/24/15.

from __future__ import absolute_import

from django.conf import settings
from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainsite.settings_local')
app = Celery('mainsite')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

