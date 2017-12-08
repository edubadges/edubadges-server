import os
import re

from setuptools import find_packages, setup

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()


setup(
    name='badgr-server',
    version='2.0.23',

    package_dir={'': "apps"},
    packages=find_packages('apps'),
    include_package_data=True,

    license='GNU Affero General Public License v3',
    description='Digital badge management for issuers, earners, and consumers',
    long_description=README,
    url='https://badgr.io/',
    author='Concentric Sky',
    author_email='badgr@concentricsky.com',

    install_requires=[
        # Django stuff
        "Django==1.10.7",
        "semver==2.6.0",
        "pytz==2017.2",
        # PIL support
        "Pillow>=2.6.1,<3",

        # mysql database
        "MySQL-python==1.2.5",

        # Email support
        "boto==2.33.0",
        "django-boto==0.3.12",
        "django-ses==0.6.0",
        "django-storages==1.6.5",
        "pycurl==7.43.0",
        "boto3==1.4.7",


        "python-resize-image==1.1.10",

        # CSky models
        "django-cachemodel==2.1.7",
        "django-basic-models==3.0.2",
        "django-ismigrated==1.0.0",

        "django-object-actions==0.8.2",

        "python-memcached==1.58",

        "djangorestframework==3.6.2",

        # Django Allauth
        "django-allauth==0.32.0",
        "oauthlib==2.0.2",
        "requests==2.18.1",
        "requests-oauthlib==0.4.2",
        # Permissions framework
        "rules==0.4",

        # OAuth
        "django-oauth-toolkit==1.0.0",

        # Some extras
        "django-cors-headers==1.1.0",
        "django-autoslug==1.9.3",
        "wsgiref==0.1.2",
        "sqlparse==0.1.14",
        "netaddr",

        # Utilities for working with badges
        "jsonschema==2.6.0",
        "simplejson==3.6.4",

        # JSON-LD
        "PyLD==0.7.1",
        "rfc3987==1.3.4",
        "pypng==0.0.18",
        "jsonfield==2.0.2",
        "PyJWT==1.4.0",

        # markdown support
        "Markdown==2.6.8",
        "django-markdownify==0.1.0",
        "bleach==2.0.0",

        # Badgr related utilities
        "openbadges-bakery==1.0.0b3",

        "celery==4.1.0",
        "django-celery-results==1.0.1",
        "python-json-logger==0.1.2",

        # SSL Support
        "cffi==1.2.1",
        "cryptography==1.0.2",
        "enum34==1.0.4",
        "idna==2.5",
        "ipaddress==1.0.14",
        "pyasn1==0.1.9",
        "pycparser==2.14",
        "six==1.9.0",

        #svg 2 png support
        "CairoSVG==1.0.22",
        "cssselect==0.9.2",
        "tinycss==0.4",

        # Backport of Python 3.0 CSV package with Unicode support
        "backports.csv==1.0.4",

        # EncryptedCursorPagination dependencies
        "more-itertools==2.5.0",

        "openbadges==1.0.1",
        "apispec==0.22.0",

        "apispec-djangorestframework==1.0.5",
    ],
    dependency_links=[
        "git+https://github.com/concentricsky/django-cachemodel.git@v2.1.7#egg=django-cachemodel-2.1.7",
        "git+https://github.com/concentricsky/django-basic-models.git@v3.0.2#egg=django-basic-models-3.0.2",
        "git+https://github.com/concentricsky/django-ismigrated.git@v1.0.0#egg=django-ismigrated-1.0.0",
        "git+https://github.com/concentricsky/apispec-djangorestframework.git@v1.0.5#egg=apispec-djangorestframework-1.0.5",
        "git+https://github.com/concentricsky/openbadges-bakery.git@1.0.0b3#egg=openbadges-bakery-1.0.0b3",
    ],



    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Education',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],

)
