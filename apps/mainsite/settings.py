import os
import sys

from mainsite import TOP_DIR

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
    # 'django_extensions',
    'graphene_django',
    'markdownify',
    'badgeuser',
    'allauth',
    'allauth.account',
    'social_django',
    'allauth.socialaccount',
    'badgrsocialauth.providers.eduid',
    'badgrsocialauth.providers.surf_conext',
    'badgrsocialauth.providers.surfconext_ala',
    'badgrsocialauth.providers.kony',
    'badgrsocialauth.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.azure',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.oauth2',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_results',

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
    # 'mainsite.middleware.MaintenanceMiddleware',
    'badgeuser.middleware.InactiveUserMiddleware',
    # 'mainsite.middleware.TrailingSlashMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',

]

ROOT_URLCONF = 'mainsite.urls'

# Hosts/domain names that are valid for this site.
# "*" matches anything, ".example.com" matches example.com and all subdomains

ALLOWED_HOSTS = ['*', ] # ['<your badgr server domain>', ]
#X_FRAME_OPTIONS = 'ALLOW-FROM http://canvas.edubadges.nl/, https://canvas.edubadges.nl'
# X_FRAME_OPTIONS = 'ALLOW-FROM https://canvas.edubadges.nl'

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
                # 'django.template.context_processors.request',
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

HTTP_ORIGIN = os.environ.get('SERVER_PROTOCOL', '') + os.environ.get('SERVER_NAME', '')
HTTP_ORIGIN = 'http://localhost:8000' if HTTP_ORIGIN is '' else HTTP_ORIGIN

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_ROOT = os.path.join(TOP_DIR, 'staticfiles')
STATIC_URL = HTTP_ORIGIN+'/static/'
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

    # Object permissions for issuing badges
    'rules.permissions.ObjectPermissionBackend',

    # Needed to login by username in Django admin, regardless of `allauth`
    "badgeuser.backends.CachedModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "badgeuser.backends.CachedAuthenticationBackend"

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
ACCOUNT_UNIQUE_EMAIL=False
ACCOUNT_FORMS = {
    'add_email': 'badgeuser.account_forms.AddEmailForm'
}
ACCOUNT_SIGNUP_FORM_CLASS = 'badgeuser.forms.BadgeUserCreationForm'


SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'
SOCIALACCOUNT_PROVIDERS = {
    'kony': {
        'environment': 'dev'
    }
}
SOCIALACCOUNT_ADAPTER = 'badgrsocialauth.adapter.BadgrSocialAccountAdapter'

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
CORS_URLS_REGEX = r'^.*$'
CORS_MODEL = 'mainsite.BadgrApp'

CORS_EXPOSE_HEADERS = (
    'link',
)

##
#
#  Media Files
#
##

MEDIA_ROOT = os.path.join(TOP_DIR, 'mediafiles')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL+'admin/'


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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler'
        },

        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,

        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },

        # Badgr.Events emits all badge related activity
        'Badgr.Events': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        }

    },
    'formatters': {
        'default': {
            'format': '%(asctime)s %(levelname)s %(module)s %(message)s'
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
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'KEY_PREFIX': 'badgr_',
        'KEY_PREFIX': 'badgr_',
        'VERSION': 10,
        'TIMEOUT': None,
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
    'ALLOWED_VERSIONS': ['v1','v2'],
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

CAIROSVG_VERSION_SUFFIX = "2"

SITE_ID = 1

USE_I18N = True
USE_L10N = False
USE_TZ = True

BADGR_APP_ID = 1


##
#
# Markdownify
#
##

MARKDOWNIFY_WHITELIST_TAGS = [
    'h1','h2','h3','h4','h5','h6',
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
    'ACCESS_TOKEN_EXPIRE_SECONDS':  86400

}
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'

OAUTH2_TOKEN_SESSION_TIMEOUT_SECONDS = OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']

API_DOCS_EXCLUDED_SCOPES = ['rw:issuer:*', 'r:assertions', '*']


BADGR_PUBLIC_BOT_USERAGENTS = [
    'LinkedInBot',   # 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'
    'Twitterbot',    # 'Twitterbot/1.0'
    'facebook',      # https://developers.facebook.com/docs/sharing/webmasters/crawler
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

# If enabled, notify badgerank about new badgeclasses
BADGERANK_NOTIFY_ON_BADGECLASS_CREATE = True
BADGERANK_NOTIFY_ON_FIRST_ASSERTION = True
BADGERANK_NOTIFY_URL = 'https://api.badgerank.org/v1/badgeclass/submit'


from cryptography.fernet import Fernet
PAGINATION_SECRET_KEY = Fernet.generate_key()
AUTHCODE_SECRET_KEY = Fernet.generate_key()

AUTHCODE_EXPIRES_SECONDS = 600  # needs to be long enough to fetch information from socialauth providers

SESSION_COOKIE_SAMESITE = None

GRAPHENE = {
    'SCHEMA': 'apps.mainsite.schema.schema'
}