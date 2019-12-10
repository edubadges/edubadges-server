import os

from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand
from django.core.management import call_command
from django.test.runner import setup_databases
from mainsite import TOP_DIR


class Command(RunserverCommand):
    args = ''
    help = 'Builds a test database, and runs a test runserver'

    def handle(self, *args, **options):
        if len(args) < 1:
            args = ["8001"]
        if not options.get('settings'):
            os.environ['DJANGO_SETTINGS_MODULE'] = 'mainsite.settings_testserver'
        setup_databases(verbosity=1, interactive=False)
        call_command("loaddata", os.path.join(TOP_DIR, "fixtures", "testserver.json"))
        return super(Command, self).handle(*args, **options)
