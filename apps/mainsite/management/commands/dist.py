from django.core import management
from django.core.management.base import BaseCommand
from subprocess import call


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        """
        Builds gulp resources.
        Gulp must be installed, and node_modules must be populated with `npm install`
        """
        call(['grunt', 'dist'])
        #management.call_command('test', verbosity=1)
