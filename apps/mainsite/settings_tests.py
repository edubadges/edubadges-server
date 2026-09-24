# encoding: utf-8


from .settings import *

PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

# disable logging for tests
LOGGING = {}
DISABLE_AUTH_SIGNALS = True
ENABLE_EXTENSION_VALIDATION = False
