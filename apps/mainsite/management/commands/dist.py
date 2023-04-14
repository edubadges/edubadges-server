import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from mainsite import TOP_DIR


class Command(BaseCommand):
    args = ''
    help = 'Runs build tasks to compile javascript and css'

    def handle(self, *args, **options):
        dirname = os.path.join(TOP_DIR, 'apps', 'mainsite', 'static')
        if not os.path.exists(dirname):
            os.makedirs(dirname)

