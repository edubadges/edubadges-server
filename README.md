![Edubadges](logo.png)
# Edubadges Server (Backend)

[![Build Status](https://travis-ci.com/edubadges/edubadges-server.svg?branch=master)](https://travis-ci.com/edubadges/edubadges-server)
[![codecov](https://codecov.io/gh/edubadges/edubadges-server/branch/master/graph/badge.svg)](https://codecov.io/gh/edubadges/edubadges-server)

*Digital badge management for issuers, earners, and consumers*

Edubadges server is the Python/Django API backend for issuing edubadges. Edubadges are digital credentials that use the [Open Badges](https://openbadges.org/) standard. In addition to a powerful issuer API and browser-based user interface for issuing, Edubadges offers integrated badge management and sharing for badge earners.

See also [edubadges-ui](https://github.com/edubadges/edubadges-ui), the Svelte frontend that serves as the user interface for this project.

This software is based on the Badgr software from [Concentric Sky](https://github.com/concentricsky/).

## What are (edu)badges?
A badge is a digital piece of evidence with which a student demonstrates that he or she has mastered certain skills or knowledge. In the context of lifelong development, students and employees are increasingly being educated or gaining experience at various institutions, both in their own country and abroad. Badges are a great instrument to make acquired knowledge and skills visible and 'portable'.

## Edubadges and microcredentialing
Institutions are looking into the possibilities of using digital certification for (partial) results obtained by their students. Since 2018 SURF works with various educational institutions to build a digital infrastructure with the purpose to be able to issue such digital certificates, or 'edubadges'.

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
* `virtualenv .venv`
* `source .venv/bin/activate` *Activate the environment (each time you start a session working with the code)*

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

if on a mac mysqlclient does not build, try:
```
LDFLAGS=-L/usr/local/opt/openssl/lib pip install mysqlclient
```

### Customize local settings to your environment
* `cp env_vars.sh.example env_vars.sh`
* Edit the env_vars.sh file and insert local credentials for DATABASES and email, then run the following from within the `edubadges-server` directory after sourcing the env_vars.sh:

### Migrate databases, build front-end components
* `./manage.py migrate` - set up database tables
* `./manage.py dist` - generate docs swagger file(s)

### Seed database
* `./manage.py seed -c` - truncate tables and refill with seed data
* `./manage.py seed` - fill tables with seed data if objects don't exist yet

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
* `GOOGLE_ANALYTICS_ID`
  - Google Analytics code will be inserted into your pages if this is set to your account tracking code, e.g. 'UA-3929083373-2'. See https://support.google.com/analytics/answer/1008080
* `PINGDOM_MONITORING_ID`
  - If you use Pingdom to monitor site performance, including this setting will embed Pingdom tracking script into the header.
* `OPEN_FOR_SIGNUP = True`
  - This defaults to True, but allows you to turn off signup if you would like to use Badgr for only single-account use or to manually create all users in `/staff`.
* `PAGINATION_SECRET_KEY`
  - Key used for symmetrical encryption of pagination cursors.  If not defined, encryption is disabled.  Must be 32 byte, base64-encoded random string.  For example: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"
