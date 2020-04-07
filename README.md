![Edubadges](logo.png)
# Edubadges Server (Backend)

*Digital badge management for issuers, earners, and consumers*

EduBadges server is the Python/Django API backend for issuing [Open Badges](http://openbadges.org). In addition to a powerful Issuer API and browser-based user interface for issuing, Edubadges offers integrated badge management and sharing for badge earners.

See also [edubadges-ui](https://github.com/edubadges/edubadges-ui), the Svelte front end that serves as users' interface for this project.

This software is based on the Badgr software from [Concentric Sky](https://github.com/concentricsky/).

## Edubadges and microcredentialing
Institutions are looking into the possibilities of using digital certification for (partial) results obtained by their students. In 2019, SURF will work with various institutions to continue to build a digital infrastructure with the purpose to be able to issue such digital certificates, or 'edubadges'.

## Edubadges: tool for flexible education
An increasing number of students have − whether previously or elsewhere − acquired skills and knowledge relevant to their study, and they wish to receive recognition or exemption for this in their study programme. A number of institutions are looking into the possibility of providing courses in accredited units that are smaller than a diploma (micro-credentials). Digital badges are the tools to achieve this. As these badges are issued in an educational context, they are called 'edubadges'.
Read more on [edubadges.nl](https://www.surf.nl/en/edubadges-national-approach-to-badges-in-education).

### About the Badgr Project
Badgr was developed by [Concentric Sky](https://concentricsky.com), starting in 2015 to serve as an open source reference implementation of the Open Badges Specification. It provides functionality to issue portable, verifiable Open Badges as well as to allow users to manage badges they have been awarded by any issuer that uses this open data standard. Since 2015, Badgr has grown to be used by hundreds of educational institutions and other people and organizations worldwide. See [Project Homepage](https://badgr.org) for more details about contributing to and integrating with Badgr.

# Edubadges installation instructions
## How to get started on your local development environment.
Prerequisites:

* git
* python 3.7.6
* virtualenv
* mysql
* [cairo](https://www.cairographics.org/download/) (SVG utility)

#### Optional extras:

* memcached
* amqp broker (e.g. RabbitMQ)

#### System-specific requirements:
* OS X: [XCode Command line tools](http://osxdaily.com/2014/02/12/install-command-line-tools-mac-os-x/)
* Ubuntu 12.04 (install packages with apt-get): git, git-core, python-virtualenv, gcc, python-pip, python-devel, libjpeg-turbo, libjpeg-turbo-devel, zlib-devel, mariadb-devel, openldap-devel, cyrus-sasl-devel, swig, libxslt-devel, automake, autoconf, libtool, libffi-devel
* CentOS 7.x (install packages with yum): git, git-core, python-virtualenv, gcc, python-pip, python-devel, libjpeg-turbo, libjpeg-turbo-devel, zlib-devel, mariadb-devel, openldap-devel, cyrus-sasl-devel, swig, libxslt-devel, automake, autoconf, libtool, libffi-devel

Note: some of these packages would introduce additional security considerations if left installed on a server used in production.

### Create project directory and environment

* `mkdir edubadges && cd edubadges`
* `virtualenv env`
* `source env/bin/activate` *Activate the environment (each time you start a session working with the code)*

*Obtain source code and clone into code directory*

* `git clone https://github.com/edubadges/edubadges-server.git`
* `cd edubadges-server`
* `git submodule update --init`

### Create database
```
DROP DATABASE IF EXISTS badgr;
CREATE DATABASE badgr CHARACTER SET utf8 DEFAULT COLLATE utf8_general_ci;
```

### Install requirements
*from within edubadges-server directory*

* `pip install -r requirements.txt`
* `pip install -r apps/ims/requirements.txt`

### Customize local settings to your environment
* `cp apps/mainsite/settings_local.py.example apps/mainsite/settings_local.py`
* Edit the settings_local.py file and insert local credentials for DATABASES and email, then run the following from within the `edubadges-server` directory:

### Migrate databases, build front-end components
* `./manage.py migrate` - set up database tables
* `./manage.py dist` - generate docs swagger file(s)

### Seed database
* set `ALLOW_SEEDS = True` in settings_local.py
* set `EDU_ID_SECRET` and `SURF_CONEXT_SECRET` to appropriate values in settings_local.py
* `./manage.py seed` - truncate tables and refill with seed data

### Run a server locally for development
* `./manage.py runserver`

### See all url's
* `./manage.py show_urls`

### Staff dashboard
* `/staff/superlogin`
    * You can log in on the [staff dashboard](http://localhost:8000/staff/superlogin) with your superuser credentials (if you ran the seeds these will be username: superuser, password: secret).
* `/docs`
    * [API documentation](http://localhost:8000/docs)

### Additional configuration options
Set these values in your settings_local.py file to configure the application to your specific needs. Required options are listed in bold.
* `HELP_EMAIL` (Required)
  - An email address for your support staff.
* `BADGR_APPROVED_ISSUERS_ONLY`
  - If you choose to use the BADGR_APPROVED_ISSUERS_ONLY flag, this means new user accounts will not be able to define new issuers (though they can be added as staff on issuers defined by others) unless they have the Django user permission 'issuer.add_issuer'. The recommended way to grant users this privilege is to create a group that grants it in the `/staff` admin area and addthe appropriate users to that group.
* `GOOGLE_ANALYTICS_ID`
  - Google Analytics code will be inserted into your pages if this is set to your account tracking code, e.g. 'UA-3929083373-2'. See https://support.google.com/analytics/answer/1008080
* `PINGDOM_MONITORING_ID`
  - If you use Pingdom to monitor site performance, including this setting will embed Pingdom tracking script into the header.
* `CELERY_ALWAYS_EAGER = True`
  - Celery is an asynchronous task runner built into Django and Edubadges. Advanced deployments may separate celery workers from web nodes for improved performance. For development environments where Celery tasks should run synchronously, set this flag to true. Very few tasks are part of this repository, and eager is a safe setting for most production deploys.
* `OPEN_FOR_SIGNUP = True`
  - This defaults to True, but allows you to turn off signup if you would like to use Badgr for only single-account use or to manually create all users in `/staff`.
* `PAGINATION_SECRET_KEY`
  - Key used for symmetrical encryption of pagination cursors.  If not defined, encryption is disabled.  Must be 32 byte, base64-encoded random string.  For example: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"