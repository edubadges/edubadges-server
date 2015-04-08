# Badgr Platform
*Digital badge management for issuers, earners, and consumers*

## How to get started on your local development environment.
This is a 
Prerequisites:
  * python 2.7.x
  * virtualenv
  * npm
  - gulp (optional global install, or fallback with npm run-script )

### Create project directory and environment
mkdir <PROJECT>
cd <PROJECT>

*It is sometimes useful to be able to easily switch between different version of the environment:*
virtualenv env-<CURRENT DATE>
ln -s env-<CURRENT DATE> env

*Activate the environment (each time you start a session working with the code)*
source env/bin/activate

*Obtain source code*
#### TODO: switch to master branch
git clone ssh://git@stash.concentricsky.com/~notto/badgr-platform.git -b develop code
cd code

### Install requirements
pip install -r requirements.txt
npm install

### Customize local settings to your environment
cp apps/mainsite/settings_local.py.example apps/mainsite/settings_local.py

* Edit the settings_local.py file and insert local credentials for DATABASES, Email, then run the following from within the `code` directory:

### Migrate databases and build front-end components
./manage.py migrate
gulp

./manage py createsuperuser

### Run a server
./manage.py runserver
Navigate to http://localhost:8000/accounts/login
login as superuser, verify an email address

