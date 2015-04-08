from django.core.management.base import BaseCommand, CommandError
from subprocess import check_call


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        self.stdout.write('Task `dist`: compile front end resources with npm version...')

        check_call(['npm','-v'])
        check_call(['npm', 'install'])
        check_call(['npm', 'run-script', 'gulp-build'])

        self.stdout.write('SUCCESS: compiled front end resources')
