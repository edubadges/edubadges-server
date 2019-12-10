# encoding: utf-8


from .settings import *

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
PAGINATION_SECRET_KEY = Fernet.generate_key()
AUTHCODE_SECRET_KEY = Fernet.generate_key()
DEFAULT_DOMAIN = 'https://badgr-pilot2.edubadges.nl'
