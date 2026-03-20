from .settings import *

# Override settings that require environment variables for build-time operations
DOMAIN = 'build.example.com'
UI_URL = 'http://build.example.com'
DEFAULT_DOMAIN = 'http://build.example.com'

# Override any other settings that might cause issues during build
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
AWS_STORAGE_BUCKET_NAME = None

# Use local storage for static files during build
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}
