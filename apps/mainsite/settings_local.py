# settings_local.py is for all instance specific settings
from .settings import *
from mainsite import TOP_DIR
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_ERRORS = DEBUG
DEBUG_STATIC = DEBUG
DEBUG_MEDIA = DEBUG
TIME_ZONE = 'America/Los_Angeles'
LANGUAGE_CODE = 'en-us'


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


ACCOUNT_SALT = os.environ['ACCOUNT_SALT']
STAFF_MEMBER_CONFIRMATION_EXPIRE_DAYS = 7

# celery
BROKER_URL = 'amqp://localhost:5672/'
CELERY_RESULT_BACKEND = None
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULTS_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

SURFCONEXT_DOMAIN_URL = 'https://oidc.test.surfconext.nl'

EDUID_RELYING_PARTY_HOST = os.environ['EDUID_RELYING_PARTY_HOST'] # your host
EDUID_REDIRECT_URL = os.environ['EDUID_REDIRECT_URL'] # url to your callback
EDUID_PROVIDER_URL = "https://eduid.pilot.acc.eduid.nl"

# Optionally restrict issuer creation to accounts that have the 'issuer.add_issuer' permission
# Niet elke issuer mag issuers aanmaken
BADGR_APPROVED_ISSUERS_ONLY = True

# If you have an informational front page outside the Django site that can link back to '/login', specify it here
ROOT_INFO_REDIRECT = '/login'
SECRET_KEY = os.environ['ROOT_INFO_SECRET_KEY']
UNSUBSCRIBE_SECRET_KEY = os.environ['UNSUBSCRIBE_SECRET_KEY']

LOGS_DIR = TOP_DIR + '/logs'
# Run celery tasks in same thread as webserver
CELERY_ALWAYS_EAGER = True

EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT= os.environ['EMAIL_PORT']
DEFAULT_FROM_EMAIL = os.environ['DEFAULT_FROM_EMAIL']

# INSTALLED_APPS.append('django_extensions')

LOGS_DIR = os.path.join(TOP_DIR, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        # badgr events log to disk by default
        'badgr_events': {
            'level': 'INFO',
            'formatter': 'json',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOGS_DIR, 'badgr_events.log')
        },
        'badgr_debug' : {
            'level': 'INFO',
            'formatter': 'badgr',
            'class': 'logging.handlers.RotatingFileHandler',
            'maxBytes': 15728640,  # 1024 * 1024 * 15B = 15MB
            'backupCount': 40,
            'filename': os.path.join(LOGS_DIR, 'badgr_debug.log')
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # Badgr.Events emits all badge related activity
        'Badgr.Events': {
            'handlers': ['badgr_events'],
            'level': 'INFO',
            'propagate': False,
        },
         'Badgr.Debug' : {
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
            'format': '%(asctime)s | %(levelname)s | %(funcName)s | %(pathname)s:%(lineno)d | %(message)s'
        },
        'json': {
            '()': 'mainsite.formatters.JsonFormatter',
            'format': '%(asctime)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        }
    },
}

TIME_STAMPED_OPEN_BADGES_BASE_URL = os.environ['TIME_STAMPED_OPEN_BADGES_BASE_URL']
PERMISSION_GROUPS = ['']

DOMAIN = os.environ['DOMAIN']
UI_URL = os.environ['UI_URL_HTTP']
DEFAULT_DOMAIN = os.environ['DEFAULT_DOMAIN']
HTTP_ORIGIN = DEFAULT_DOMAIN
HTTP_ORIGIN_MEDIA = DEFAULT_DOMAIN

MIDDLEWARE += [
    'corsheaders.middleware.CorsMiddleware',
]

CORS_ORIGIN_WHITELIST = [
    os.environ['UI_URL_HTTP'],
    os.environ['UI_URL_HTTPS'],
]
CORS_ALLOW_CREDENTIALS = True

ALLOW_SEEDS = True
EDU_ID_SECRET = os.environ['EDU_ID_SECRET']
EDU_ID_CLIENT = "edubadges"

SURF_CONEXT_SECRET = os.environ['SURF_CONEXT_SECRET']
SURF_CONEXT_CLIENT = "http@//localhost.edubadges.nl"

SUPERUSER_NAME = os.environ['SUPERUSER_NAME']
SUPERUSER_EMAIL = os.environ['SUPERUSER_EMAIL']
SUPERUSER_PWD = os.environ['SUPERUSER_PWD']
