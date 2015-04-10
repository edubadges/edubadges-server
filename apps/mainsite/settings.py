import sys
import os

from mainsite import TOP_DIR


##
#
#  Important Stuff
#
##

INSTALLED_APPS = [
    # https://github.com/concentricsky/django-client-admin
    'client_admin',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'badgeuser',

    'allauth',
    'allauth.account',

    # 'skycms.structure',
    'reversion',
    'jingo',
    # 'djangosphinx',
    # 'sky_thumbnails',
    # 'ckeditor',
    # 'sky_redirects',
    # 'emailtemplates',
    # 'sky_visitor',

    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',

    'mainsite',
    'issuer',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mainsite.middleware.MaintenanceMiddleware',
    # 'mainsite.middleware.TrailingSlashMiddleware',
]

ROOT_URLCONF = 'mainsite.urls'

SECRET_KEY = '{{secret_key}}'

# Hosts/domain names that are valid for this site.
# "*" matches anything, ".example.com" matches example.com and all subdomains
ALLOWED_HOSTS = ['*', ]

##
#
#  Templates
#
##

TEMPLATE_LOADERS = [
    'jingo.Loader',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

TEMPLATE_DIRS = [
    os.path.join(TOP_DIR, 'breakdown', 'templates'),
]

TEMPLATE_CONTEXT_PROCESSORS = [
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.i18n',

    # allauth specific context processors
    "allauth.account.context_processors.account",
    "allauth.socialaccount.context_processors.socialaccount",
]

JINGO_EXCLUDE_APPS = (
    'admin',
    'registration',
    'debug_toolbar',
    'ckeditor',
    'reversion',
    'rest_framework',
    'allauth',
    'account',
    'rest_framework_swagger'
)


##
#
#  Static Files
#
##

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_ROOT = os.path.join(TOP_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(TOP_DIR, 'breakdown', 'static'),
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
    # Object permissions for issuing badges
    'rules.permissions.ObjectPermissionBackend',

    # Needed to login by username in Django admin, regardless of `allauth`
    "django.contrib.auth.backends.ModelBackend",

    # `allauth` specific authentication methods, such as login by e-mail
    "allauth.account.auth_backends.AuthenticationBackend",
]
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True

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
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
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

SPHINX_API_VERSION = 0x116 # Sphinx 0.9.9


##
#
#  CKEditor
#
##

# https://github.com/concentricsky/django-sky-ckeditor
CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            [      'Undo', 'Redo',
              '-', 'Format',
              '-', 'Bold', 'Italic', 'Underline',
              '-', 'Link', 'Unlink',
              '-', 'BulletedList', 'NumberedList',
            ],
            [      'SpellChecker', 'Scayt',
            ],
            [      'Image',
              '-', 'PasteText','PasteFromWord',
              '-', 'Source',
            ]
        ],
        'contentsCss': STATIC_URL+'css/ckeditor.css',
        'format_tags': 'p;h3;h4',
        'width': 655,
        'height': 250,
        'toolbarCanCollapse': False,
        'debug': True,
        'linkShowTargetTab': False,
        'linkShowAdvancedTab': False,
    }
    , 'basic': {
        'toolbar': [
            [      'Bold', 'Italic',
              '-', 'Link', 'Unlink',
            ]
        ]
        , 'width': 600
        , 'height': 250
        , 'toolbarCanCollapse': False
        , 'toolbarLocation': 'bottom'
        , 'resize_enabled': False
        , 'removePlugins': 'elementspath'
        , 'forcePasteAsPlainText': True
    }
}

CKEDITOR_EMBED_CONTENT = ['structure.page', 'structure.fileupload']


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
    )
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

SITE_ID = 1

USE_I18N = False
USE_L10N = False
USE_TZ = True


##
#
#  Import settings_local.
#
##

try:
    from settings_local import *
except ImportError as e:
    import sys
    sys.stderr.write("no settings_local found, setting DEBUG=True...\n")
    DEBUG = True
    pass
