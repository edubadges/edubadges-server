import os

from mainsite import TOP_DIR
from mainsite.environment import env_settings


def legacy_boolean_parsing(env_key, default_value):
    val = os.environ.get(env_key, default_value)
    val = '1' if val == 'True' else '0' if val == 'False' else val
    return bool(int(val))


env_settings()

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
    'graphene_django',
    'django_extensions',
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
    'rest_framework_swagger',

    # OAuth 2 provider
    'oauth2_provider',

    'entity',
    'ims',
    'institution',
    'issuer',
    'backpack',
    'lti_edu',
    'theming',
    'signing',
    'staff',

    # api docs
    'apispec_drf',

    # deprecated
    'composition',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'badgeuser.middleware.InactiveUserMiddleware',
    'mainsite.middleware.ExceptionHandlerMiddleware',
    'mainsite.middleware.RequestResponseLoggerMiddleware',
    # 'mainsite.middleware.MaintenanceMiddleware',
    # 'mainsite.middleware.TrailingSlashMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',

]

ROOT_URLCONF = 'mainsite.urls'
ALLOWED_HOSTS = ['*', ]
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
                'mainsite.context_processors.extra_settings'
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
LOGIN_REDIRECT_URL = '/docs'

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    # Needed to login by username in Django admin, regardless of `allauth`
    "badgeuser.backends.CachedModelBackend",
]

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_ADAPTER = 'mainsite.account_adapter.BadgrAccountAdapter'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_AUTHENTICATION_METHOD = 'username'
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'username'
ACCOUNT_UNIQUE_EMAIL = False
ACCOUNT_FORMS = {
    'add_email': 'badgeuser.account_forms.AddEmailForm'
}
ACCOUNT_SIGNUP_FORM_CLASS = 'badgeuser.forms.BadgeUserCreationForm'
ACCOUNT_SALT = os.environ['ACCOUNT_SALT']

SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_ADAPTER = 'badgrsocialauth.adapter.BadgrSocialAccountAdapter'

SURFCONEXT_DOMAIN_URL = os.environ.get('SURFCONEXT_DOMAIN_URL', 'https://oidc.test.surfconext.nl/oidc')
EDUID_PROVIDER_URL = os.environ['EDUID_PROVIDER_URL']
EDUID_REGISTRATION_URL = os.environ['EDUID_REGISTRATION_URL']

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
        }
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
##

LOGS_DIR = os.path.join(TOP_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

LOG_STORAGE_DURATION = 30  # days

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'badgr_events': {
            'level': 'INFO',
            'formatter': 'json',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'H',
            'interval': 1,
            'backupCount': 30*24,  # 30 days times 24 hours
            'filename': os.path.join(LOGS_DIR, 'badgr_events.log')
        },
        'badgr_debug': {
            'level': 'INFO',
            'formatter': 'badgr',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'H',
            'interval': 1,
            'backupCount': 30*24,  # 30 days times 24 hours
            'filename': os.path.join(LOGS_DIR, 'badgr_debug.log')
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'Badgr.Events': {
            'handlers': ['badgr_events'],
            'level': 'INFO',
            'propagate': False,
        },
        'Badgr.Debug': {
            'handlers': ['badgr_debug'],
            'level': 'INFO',
            'propagate': True,
        }
    },
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(module)s %(message)s'
        },
        'badgr': {
            'format': '%(asctime)s | %(levelname)s | %(message)s'
        },
        'json': {
            '()': 'mainsite.formatters.JsonFormatter',
            'format': '%(asctime)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        }
    },
}

##
#
#  Caching
#
##

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': 'localhost:11211',
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
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'DEFAULT_RENDERER_CLASSES': (
        'mainsite.renderers.JSONLDRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'mainsite.authentication.BadgrOAuth2Authentication',
        'rest_framework.authentication.TokenAuthentication',
        'entity.authentication.ExplicitCSRFSessionAuthentication',
        # 'rest_framework.authentication.BasicAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'EXCEPTION_HANDLER': 'entity.views.exception_handler'
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
CAIROSVG_VERSION_SUFFIX = "2"

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
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
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
    'hr'
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
    'ACCESS_TOKEN_EXPIRE_SECONDS': 86400

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

SESSION_COOKIE_SAMESITE = None

GRAPHENE = {
    'SCHEMA': 'apps.mainsite.schema.schema'
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['BADGR_DB_NAME'],
        'USER': os.environ['BADGR_DB_USER'],
        'PASSWORD': os.environ['BADGR_DB_PASSWORD'],
        'HOST': '',
        'PORT': '',
        'TEST': {
            'CHARSET': 'utf8',
        }
    }
}

# Email
EMAIL_USE_TLS = True
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

# Seeds
ALLOW_SEEDS = legacy_boolean_parsing('ALLOW_SEEDS', '0')
EDU_ID_SECRET = os.environ['EDU_ID_SECRET']
EDU_ID_CLIENT = os.environ.get('EDU_ID_CLIENT', "edubadges")

SURF_CONEXT_SECRET = os.environ.get('SURF_CONEXT_SECRET', 'secret')
SURF_CONEXT_CLIENT = os.environ.get('SURF_CONEXT_CLIENT', "test.edubadges.nl")

SUPERUSER_NAME = os.environ.get('SUPERUSER_NAME', '')
SUPERUSER_EMAIL = os.environ.get('SUPERUSER_EMAIL', '')
SUPERUSER_PWD = os.environ.get('SUPERUSER_PWD', '')

# Used in 01_setup sed
EDUID_BADGE_CLASS_NAME = "Edubadge account complete"

# Debug
DEBUG = legacy_boolean_parsing('DEBUG', '0')
TEMPLATE_DEBUG = DEBUG
DEBUG_ERRORS = DEBUG
DEBUG_STATIC = DEBUG
DEBUG_MEDIA = DEBUG
LOCAL_DEVELOPMENT_MODE = legacy_boolean_parsing('LOCAL_DEVELOPMENT_MODE', '0')
SUPERUSER_LOGIN_WITH_SURFCONEXT = legacy_boolean_parsing('SUPERUSER_LOGIN_WITH_SURFCONEXT', '0')

VALIDATOR_URL = os.environ.get('VALIDATOR_URL', 'http://localhost:5000')
EXTENSIONS_ROOT_URL = os.environ.get('EXTENSIONS_ROOT_URL', 'http://127.0.0.1:8000/static')


MAX_IMAGE_UPLOAD_SIZE = 256000  # 256Kb
MAX_IMAGE_UPLOAD_SIZE_LABEL = '256 kB'  # used in error messaging