import os
import pkg_resources
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from subprocess import call

import mainsite
from mainsite import TOP_DIR


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        dirname = os.path.join(TOP_DIR, 'apps', 'mainsite', 'static', 'swagger-ui')
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        call_command('generate_swagger_spec',
            output=os.path.join(dirname, 'api_spec_{version}.json'),
            preamble=os.path.join(dirname, "API_DESCRIPTION_{version}.md"),
            versions=['v1', 'v2'],
            include_oauth2_security=True
        )
