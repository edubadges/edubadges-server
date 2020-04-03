import os
import sys

# assume we(this file) have a parent that is a sibling to the CODE_DIR
OUR_DIR = os.path.abspath(os.path.dirname(__file__))

# code dir is one level above us
APPS_DIR = os.path.join(OUR_DIR, '..', 'code', 'apps')

# the env dir is one level above us
ENV_DIR = os.path.join(OUR_DIR, '..')
# remove virtual env
#, 'env')

# activate the virtualenv
# activate_this = os.path.join(ENV_DIR, 'bin', 'activate_this.py')
# exec(compile(open(activate_this, "rb").read(), activate_this, 'exec'), dict(__file__=activate_this))

# add the apps directory to the python path
sys.path.insert(0, APPS_DIR)

# load up django
from django.core.wsgi import get_wsgi_application

# tell django to find settings entry point'
os.environ['DJANGO_SETTINGS_MODULE'] = 'mainsite.settings'

# hand off to the wsgi application
application = get_wsgi_application()
