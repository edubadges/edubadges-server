# Badgr Server
*Digital badge management for issuers, earners, and consumers*

Badgr Home provides an API for issuing [Open Badges](http://openbadges.org). It will soon provide integrated badge management and sharing for badge earners and tools for inspection, exploration and discovery of Open Badges and a world of learning opportunities.

*Version: Developer Preview 0.1.1*

## How to get started on your local development environment.
Prerequisites:

  * python 2.7.x
  * virtualenv
  * npm
  * gulp

### Create project directory and environment
* `mkdir badgr-home`
* `virtualenv env`
* `source env/bin/activate` *Activate the environment (each time you start a session working with the code)*

*Obtain source code*
* `git clone git@github.com:concentricsky/badgr-home.git code`
* `cd code`

### Install requirements
 *from within code directory* 

* `pip install -r requirements.txt`
* `npm install`

### Customize local settings to your environment
* `cp apps/mainsite/settings_local.py.example apps/mainsite/settings_local.py`
* Edit the settings_local.py file and insert local credentials for DATABASES and email, then run the following from within the `code` directory:

### Migrate databases, build front-end components
* `./manage.py migrate`
* `gulp build`
* `./manage py createsuperuser`

### Run a server
* `./manage.py runserver`
* Navigate to http://localhost:8000/accounts/login
* login, verify an email address

A browseable API is available at `/v1` and documentation at `/docs`

