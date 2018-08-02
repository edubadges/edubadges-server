# encoding: utf-8
from __future__ import unicode_literals

from settings import *

# disable logging for tests
LOGGING = {}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'badgr_server',
        'OPTIONS': {
            "init_command": "SET default_storage_engine=InnoDB",
        },
    }
}

CELERY_ALWAYS_EAGER = True
SECRET_KEY = 'aninsecurekeyusedfortesting'
UNSUBSCRIBE_SECRET_KEY = str(SECRET_KEY)
