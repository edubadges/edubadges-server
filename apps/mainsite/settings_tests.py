# encoding: utf-8


from .settings import *

# disable logging for tests
LOGGING = {}
DISABLE_AUTH_SIGNALS = True
ENABLE_EXTENSION_VALIDATION = False

# Insecure but faster password hashing
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
