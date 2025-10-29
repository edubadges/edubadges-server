import logging
import os

from mainsite import TOP_DIR
from mainsite.environment import env_settings


def legacy_boolean_parsing(env_key, default_value):
    val = os.environ.get(env_key, default_value)
    val = '1' if val == 'True' else '0' if val == 'False' else val
    return bool(int(val))


env_settings()

SESSION_COOKIE_AGE = 60 * 60  # 1 hour session validity
SESSION_COOKIE_SAMESITE = None  # should be set as 'None' for Django >= 3.1
SESSION_COOKIE_SECURE = True  # should be True in case of HTTPS usage (production)

DEBUG = legacy_boolean_parsing('DEBUG', '0')

##
#
#  Important Stuff
#
##

INSTALLED_APPS = [
    'mainsite',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_object_actions',
    'cachemodel',
    'basic_models',
    'graphene_django',
    'django_extensions',
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'markdownify',
    'badgeuser',
    'allauth',
    'allauth.account',
    'social_django',
    'allauth.socialaccount',
    'badgrsocialauth.providers.eduid',
    'badgrsocialauth.providers.surf_conext',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.azure',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.oauth2',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_results',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    # OAuth 2 provider
    'oauth2_provider',
    # eduBadges apps
    'directaward',
    'endorsement',
    'badge_connect',
    'entity',
    'institution',
    'issuer',
    'backpack',
    'lti_edu',
    'theming',
    'signing',
    'staff',
    'insights',
    'queries',
    'lti13',
    'ob3',
    'notifications',
    # deprecated
    'composition',
    'auditlog',
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'lti13.middleware.SameSiteMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'badgeuser.middleware.InactiveUserMiddleware',
    'mainsite.middleware.ExceptionHandlerMiddleware',
    'mainsite.middleware.RequestResponseLoggerMiddleware',
    # 'mainsite.middleware.MaintenanceMiddleware',
    # 'mainsite.middleware.TrailingSlashMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'mainsite.urls'
ALLOWED_HOSTS = [
    '*',
]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

##
#
#  Templates
#
##

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'mainsite.context_processors.extra_settings',
            ],
        },
    },
]

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

##
#
#  Static Files
#
##

HTTP_ORIGIN = os.environ.get('SERVER_PROTOCOL', '') + os.environ.get('SERVER_NAME', '') or 'http://localhost:8000'
HTTP_ORIGIN_MEDIA = HTTP_ORIGIN

DOMAIN = os.environ['DOMAIN']
UI_URL = os.environ['UI_URL']
DEFAULT_DOMAIN = os.environ['DEFAULT_DOMAIN']

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_ROOT = os.path.join(TOP_DIR, 'staticfiles')
STATIC_URL = HTTP_ORIGIN + '/static/'
STATICFILES_DIRS = [
    os.path.join(TOP_DIR, 'apps', 'mainsite', 'static'),
]

##
#
#  User / Login / Auth
#
##

AUTH_USER_MODEL = 'badgeuser.BadgeUser'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/api/schema/redoc'

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    # Needed to login by username in Django admin, regardless of `allauth`
    'badgeuser.backends.CachedModelBackend',
]

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_ADAPTER = 'mainsite.account_adapter.BadgrAccountAdapter'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_FORMS = {'add_email': 'badgeuser.account_forms.AddEmailForm'}
ACCOUNT_SIGNUP_FORM_CLASS = 'badgeuser.forms.BadgeUserCreationForm'
ACCOUNT_SALT = os.environ['ACCOUNT_SALT']

SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_ADAPTER = 'badgrsocialauth.adapter.BadgrSocialAccountAdapter'

SURFCONEXT_DOMAIN_URL = os.environ.get('SURFCONEXT_DOMAIN_URL', 'https://connect.test.surfconext.nl/oidc')

##
# EduId, in both provider and EDUID_xxx (or EDU_ID) is a confusing name, because it's really surfconext but the surfconext setup for the students.
# A better name would be something like OIDC_STUDENT_xxx but that would be a big change as we'd need to rename socialauth providers,
# urls, views, and database migrations.

# Determines the subclass of the oidc client to use. Can be 'eduid' or 'surfconext'.
# When "eduid" is used, we *must* set the EDUID_API_BASE_URL, as this is used to build the URL
# that mimics the "userinfo" endpoint of the oidc client but has "validated name" information.
# For surfconext, the userinfo endpoint is determined from the SURFCONEXT_DOMAIN_URL.
EDUID_OIDC_PROVIDER_NAME = 'surfconext'
EDUID_PROVIDER_URL = os.environ['EDUID_PROVIDER_URL']
EDUID_API_BASE_URL = os.environ.get('EDUID_API_BASE_URL', 'https://login.test.eduid.nl')
EDUID_IDENTIFIER = os.environ.get('EDUID_IDENTIFIER', 'eduid')

EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = str(
    os.environ.get('EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS', '42, 62')
)
EXPIRY_DIRECT_AWARDS_DELETION_THRESHOLD_DAYS = int(os.environ.get('EXPIRY_DIRECT_AWARDS_DELETION_THRESHOLD_DAYS', 82))
DIRECT_AWARDS_DELETION_THRESHOLD_DAYS = int(os.environ.get('DIRECT_AWARDS_DELETION_THRESHOLD_DAYS', 30))

OB3_AGENT_URL_SPHEREON = os.environ.get('OB3_AGENT_URL_SPHEREON', '')
OB3_AGENT_AUTHZ_TOKEN_SPHEREON = os.environ.get('OB3_AGENT_AUTHZ_TOKEN_SPHEREON', '')
OB3_AGENT_URL_UNIME = os.environ.get('OB3_AGENT_URL_UNIME', '')

# If you have an informational front page outside the Django site that can link back to '/login', specify it here
ROOT_INFO_REDIRECT = '/login'
SECRET_KEY = os.environ['ROOT_INFO_SECRET_KEY']
UNSUBSCRIBE_SECRET_KEY = os.environ['UNSUBSCRIBE_SECRET_KEY']

STAFF_MEMBER_CONFIRMATION_EXPIRE_DAYS = 7

# Added property to allow auto signup on existing email address
# -> this is for the usecase that user logs in with existing email, for which
# in the case of SurfConext we trust that the passed email address is verified.
# Is used in badgrsocialauth.adapter and defaults to False
SOCIALACCOUNT_AUTO_SIGNUP = True

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        },
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

##
#
#  CORS
#
##
CORS_ALLOW_ALL_ORIGINS = True
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ('link',)

##
#
#  Media Files
#
##

MEDIA_ROOT = os.path.join(TOP_DIR, 'mediafiles')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

##
#
#   S3/MinIO Storage Configuration
#
##

# S3/MinIO configuration for file storage
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL', None)  # For MinIO
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'us-east-1')

# SSL and signature configuration
AWS_S3_USE_SSL = os.environ.get('AWS_S3_USE_SSL', 'True').lower() == 'true'
AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION', 's3v4')

# Public read permissions for badge images
AWS_DEFAULT_ACL = 'public-read'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Use custom domain if provided (for MinIO or custom S3 setup)
AWS_S3_CUSTOM_DOMAIN = os.environ.get('AWS_S3_CUSTOM_DOMAIN', None)

# Media URL configuration
if AWS_S3_CUSTOM_DOMAIN:
    _endpoint_url = f'{"https" if AWS_S3_USE_SSL else "http"}://{AWS_S3_CUSTOM_DOMAIN}/'
elif AWS_S3_ENDPOINT_URL:  # MinIO config
    from urllib.parse import urlparse

    parsed = urlparse(AWS_S3_ENDPOINT_URL)
    _endpoint_url = f'{parsed.scheme}://{parsed.netloc}/{AWS_STORAGE_BUCKET_NAME}/'
else:
    _endpoint_url = f'https://{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'

ENDPOINT_URL = _endpoint_url

STORAGES = {
    'default': {
        'BACKEND': 'mainsite.proxied_s3_storage.ProxiedS3Storage',
        'OPTIONS': {
            'access_key': AWS_ACCESS_KEY_ID,
            'secret_key': AWS_SECRET_ACCESS_KEY,
            'bucket_name': AWS_STORAGE_BUCKET_NAME,
            'region_name': AWS_S3_REGION_NAME,
            'endpoint_url': ENDPOINT_URL,
            'use_ssl': AWS_S3_USE_SSL,
            'signature_version': AWS_S3_SIGNATURE_VERSION,
            'default_acl': AWS_DEFAULT_ACL,
            'object_parameters': AWS_S3_OBJECT_PARAMETERS,
            'custom_domain': AWS_S3_CUSTOM_DOMAIN,
        },
    }
}

##
#
#   Fixtures
#
##

FIXTURE_DIRS = [
    os.path.join(TOP_DIR, 'etc', 'fixtures'),
]

##
#
#  Logging
#
#  We try to keep close to the default Django logging. Convention over configuration..
#  But we want to remove handlers that email. And want to ensure useful logs are propagated to the console
#  We set the log level, based on the DEBUG flag: DEBUG if DEBUG else INFO This is default Django behaviour
#  The container runner will add timestamp and container name to the logs
##
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'mainsite.formatters.JsonFormatter',
            'format': '%(levelname)s %(name)s %(module)s %(message)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        },
    },
    'handlers': {
        'console': {'level': LOG_LEVEL, 'class': 'logging.StreamHandler', 'formatter': 'json'},
    },
    'loggers': {
        'Badgr.Debug': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'Badgr.Events': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],  # Replace stream and email handler with console
            'level': LOG_LEVEL,
            'propagate': False,  # Don't propagate to root logger as that will cause duplicate logs
        },
    },
}

##
#
#  Caching
#
##

CACHES = {
    'default': {
        # using django_prometheus to monitor cache: https://github.com/korfuri/django-prometheus/blob/master/README.md#monitoring-your-caches
        'BACKEND': 'django_prometheus.cache.backends.memcached.PyMemcacheCache',
        'LOCATION': os.environ.get('MEMCACHED', '0.0.0.0:11211'),
    }
}

##
#
#  Maintenance Mode
#
##

MAINTENANCE_MODE = False
MAINTENANCE_URL = '/maintenance'

##
#
#  Sphinx Search
#
##

SPHINX_API_VERSION = 0x116  # Sphinx 0.9.9

##
#
# Testing
##
TEST_RUNNER = 'mainsite.testrunner.BadgrRunner'

##
#
#  REST Framework
#
##

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'],
    'DEFAULT_RENDERER_CLASSES': (
        'mainsite.renderers.JSONLDRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'mainsite.oidc_authentication.OIDCAuthentication',
        'mainsite.authentication.BadgrOAuth2Authentication',
        'entity.authentication.ExplicitCSRFSessionAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'EXCEPTION_HANDLER': 'entity.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

##
#
#  Remote document fetcher (designed to be overridden in tests)
#
##

REMOTE_DOCUMENT_FETCHER = 'badgeanalysis.utils.get_document_direct'
LINKED_DATA_DOCUMENT_FETCHER = 'badgeanalysis.utils.custom_docloader'

##
#
#  Misc.
#
##

LTI_STORE_IN_SESSION = False
TIME_STAMPED_OPEN_BADGES_BASE_URL = os.environ['TIME_STAMPED_OPEN_BADGES_BASE_URL']
CAIROSVG_VERSION_SUFFIX = '2'

USE_I18N = True
USE_L10N = False
USE_TZ = True

SITE_ID = int(os.environ.get('SITE_ID', 1))
BADGR_APP_ID = int(os.environ.get('BADGR_APP_ID', 1))

TIME_ZONE = 'Europe/Amsterdam'
LANGUAGE_CODE = 'en-us'

##
#
# Markdownify
#
##

MARKDOWNIFY_WHITELIST_TAGS = [
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'a',
    'abbr',
    'acronym',
    'b',
    'blockquote',
    'em',
    'i',
    'li',
    'ol',
    'p',
    'strong',
    'ul',
    'code',
    'pre',
    'hr',
]

OAUTH2_PROVIDER = {
    'SCOPES': {
        'r:profile': 'See who you are',
        'rw:profile': 'Update your own User profile',
        'r:backpack': "List assertions in a User's Backpack",
        'rw:backpack': "Upload badges into a User's Backpack",
        'rw:issuer': 'Create and update Issuers, create and update Badgeclasses, and award Assertions',
        # private scopes used for integrations
        'rw:issuer:*': 'Create and update Badgeclasses, and award Assertions for a single Issuer',
        'r:assertions': 'Batch receive assertions',
    },
    'DEFAULT_SCOPES': ['r:profile'],
    'OAUTH2_VALIDATOR_CLASS': 'mainsite.oauth_validator.BadgrRequestValidator',
    'ACCESS_TOKEN_EXPIRE_SECONDS': 28800,  # 28800 seconds = 8 hours
}
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'

OAUTH2_TOKEN_SESSION_TIMEOUT_SECONDS = OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']

BADGR_PUBLIC_BOT_USERAGENTS = [
    'LinkedInBot',
    # 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'
    'Twitterbot',  # 'Twitterbot/1.0'
    'facebook',  # https://developers.facebook.com/docs/sharing/webmasters/crawler
    'Facebot',
    'Slackbot',
]
BADGR_PUBLIC_BOT_USERAGENTS_WIDE = [
    'LinkedInBot',
    'Twitterbot',
    'facebook',
    'Facebot',
]

# Allow use of weaker CAs (1024 bits) to avoid problem with chained certificates used by accounts.google.com
# Ideally this environment variable would be set on a per-environment basis, only where needed
import os

import certifi

os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# default celery to always_eager
CELERY_ALWAYS_EAGER = True
BROKER_URL = 'amqp://localhost:5672/'
CELERY_RESULT_BACKEND = None
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULTS_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

from cryptography.fernet import Fernet

PAGINATION_SECRET_KEY = Fernet.generate_key()
AUTHCODE_SECRET_KEY = Fernet.generate_key()

AUTHCODE_EXPIRES_SECONDS = 600  # needs to be long enough to fetch information from socialauth providers

GRAPHENE = {'SCHEMA': 'apps.mainsite.schema.schema'}

# Database
DATABASES = {
    'default': {
        # Use of django_prometheus to monitor db: https://github.com/korfuri/django-prometheus/blob/master/README.md#monitoring-your-databases
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': os.environ['BADGR_DB_NAME'],
        'USER': os.environ['BADGR_DB_USER'],
        'PASSWORD': os.environ['BADGR_DB_PASSWORD'],
        'HOST': os.environ.get('BADGR_DB_HOST', 'localhost'),
        'PORT': os.environ.get('BADGR_DB_PORT', 5432),
        'TEST': {
            'CHARSET': 'utf8',
        },
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Email
EMAIL_USE_TLS = legacy_boolean_parsing('EMAIL_USE_TLS', '1')
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

# Seeds
ALLOW_SEEDS = legacy_boolean_parsing('ALLOW_SEEDS', '0')
EDU_ID_SECRET = os.environ['EDU_ID_SECRET']
EDU_ID_CLIENT = os.environ.get('EDU_ID_CLIENT', 'edubadges')

OIDC_RS_ENTITY_ID = os.environ.get('OIDC_RS_ENTITY_ID', 'edubadges')
OIDC_RS_SECRET = os.environ['OIDC_RS_SECRET']

SURF_CONEXT_SECRET = os.environ.get('SURF_CONEXT_SECRET', 'secret')
SURF_CONEXT_CLIENT = os.environ.get('SURF_CONEXT_CLIENT', 'test.edubadges.nl')

SUPERUSER_NAME = os.environ.get('SUPERUSER_NAME', '')
SUPERUSER_EMAIL = os.environ.get('SUPERUSER_EMAIL', '')
SUPERUSER_PWD = os.environ.get('SUPERUSER_PWD', '')

# Used in 01_setup sed
EDUID_BADGE_CLASS_NAME = 'Edubadge account complete'

# Debug
TEMPLATE_DEBUG = DEBUG
DEBUG_ERRORS = DEBUG
DEBUG_STATIC = DEBUG
DEBUG_MEDIA = DEBUG
LOCAL_DEVELOPMENT_MODE = legacy_boolean_parsing('LOCAL_DEVELOPMENT_MODE', '0')
SUPERUSER_LOGIN_WITH_SURFCONEXT = legacy_boolean_parsing('SUPERUSER_LOGIN_WITH_SURFCONEXT', '0')

VALIDATOR_URL = os.environ.get('VALIDATOR_URL', 'http://localhost:5000')
VALIDATOR_ENABLED = os.environ.get('VALIDATOR_ENABLED', False)
EXTENSIONS_ROOT_URL = os.environ.get('EXTENSIONS_ROOT_URL', 'http://127.0.0.1:8000/static')

MAX_IMAGE_UPLOAD_SIZE = 256000  # 256Kb
MAX_IMAGE_UPLOAD_SIZE_LABEL = '256 kB'  # used in error messaging

REPORT_RECEIVER_EMAIL = os.environ.get('REPORT_RECEIVER_EMAIL', '')

SPECTACULAR_SETTINGS = {
    'TITLE': 'eduBadges API',
    'DESCRIPTION': 'Edubadges are digital certificates which show that the owner has acquired certain skills or knowledge',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',  # shorthand to use the sidecar instead
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SERVERS': [{'url': os.environ['DEFAULT_DOMAIN']}],
    'PREPROCESSING_HOOKS': ['mainsite.drf_spectacluar.custom_preprocessing_hook'],
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums',
        'mainsite.drf_spectacluar.custom_postprocessing_hook',
    ],
}

AUDITLOG_DISABLE_REMOTE_ADDR = True

API_PROXY = {'HOST': OB3_AGENT_URL_UNIME}
