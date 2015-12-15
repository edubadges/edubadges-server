import os
from django.core import management
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from subprocess import call
from mainsite import TOP_DIR


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        """
        Builds gulp resources.
        Gulp must be installed, and node_modules must be populated with `npm install`
        """

        if apps.is_installed('badgebook'):
            # if badgebook is present, pull in its assets
            import pkg_resources
            import shutil
            components = pkg_resources.resource_listdir('badgebook', 'jsx')
            pkg_path = pkg_resources.resource_filename('badgebook', 'jsx')

            dest = os.path.join(TOP_DIR, 'build', 'badgebook')
            if not os.path.isdir(dest):
                os.mkdir(dest)
            for component in components:
                shutil.copy2(os.path.join(pkg_path, component), dest)

        ret = call(['grunt', 'dist'])
        if ret != 0:
            raise CommandError("grunt dist failed")
        #management.call_command('test', verbosity=1)
