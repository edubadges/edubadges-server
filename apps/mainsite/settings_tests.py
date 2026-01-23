# encoding: utf-8


from .settings import os

# disable logging for tests
LOGGING = {}
DISABLE_AUTH_SIGNALS = True
ENABLE_EXTENSION_VALIDATION = False

# Use the existing database for tests instead of creating a new one
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.mysql',
        'NAME': os.environ['BADGR_DB_NAME'],
        'USER': os.environ['BADGR_DB_USER'],
        'PASSWORD': os.environ['BADGR_DB_PASSWORD'],
        'HOST': os.environ.get('BADGR_DB_HOST', 'localhost'),
        'PORT': os.environ.get('BADGR_DB_PORT', 3306),
        'TEST': {
            'NAME': os.environ['BADGR_DB_NAME'],  # Use the same database for tests
            'CHARSET': 'utf8',
            'SERIALIZE': False,  # Don't serialize the database
            'CREATE_DB': False,  # Don't try to create the test database
            'CREATE_USER': False,  # Don't try to create a test user
        },
    }
}

# Disable database creation for tests
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
TEST_NON_SERIALIZED_APPS = ['*']
