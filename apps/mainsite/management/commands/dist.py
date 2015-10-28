from django.core import management
from django.core.management.base import BaseCommand, CommandError
from subprocess import call


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        """
        Builds gulp resources.
        Gulp must be installed, and node_modules must be populated with `npm install`
        """
        ret = call(['grunt', 'dist'])
        if ret != 0:
            raise CommandError("grunt dist failed")
        #management.call_command('test', verbosity=1)
