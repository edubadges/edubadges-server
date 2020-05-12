import traceback

from django.core.management.base import BaseCommand
from django.db import connection

from mainsite.models import BadgrApp


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--clean', action="store_true")
        parser.add_argument('-i', '--init', action="store_true")

    def handle(self, *args, **options):
        if options['clean']:
            clear_data()
        run_seed = True
        if options['init']:
            run_seed = BadgrApp.objects.count() == 0

        if run_seed:
            print("Running setup seeds... ", end="")
            try:
                __import__("mainsite.seeds.01_setup")
                print("\033[92mdone!\033[0m")
            except:
                print("\033[91mFAILED!\033[0m")
                traceback.print_exc()
        else:
            print("Skipping setup seeds... ", end="")


def clear_data():
    with connection.cursor() as cursor:
        print("Wiping data... ", end="")

        seed_filled_tables = (
            'badgeuser_termsversion',
            'socialaccount_socialapp',
            'django_site',
            'mainsite_badgrapp',
            'institution_institution',
            'institution_faculty',
            'issuer_issuer',
            'issuer_badgeclass'
        )

        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            [cursor.execute("TRUNCATE TABLE " + table) for table in seed_filled_tables]
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        print("\033[92mdone!\033[0m")
