from django.core.management.base import BaseCommand, CommandError
from subprocess import call


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        call(['gulp', 'build'])
        self.stdout.write('Successfully compiled front end resources')
