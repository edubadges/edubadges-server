from django.core.management.base import BaseCommand
from django.db import connection
import traceback

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--clean', action="store_true")


    def handle(self, *args, **options):
        if options['clean']:
            clear_data()

        print("Running setup seeds... ", end = "")
        try:
            __import__("mainsite.seeds.01_setup")
            print("\033[92mdone!\033[0m")
        except:
            print("\033[91mFAILED!\033[0m")
            traceback.print_exc()


def clear_data():
    with connection.cursor() as cursor:
        print("Wiping data... ", end = "")

        seed_filled_tables = (
            'badgeuser_termsversion',
            'socialaccount_socialapp',
            'django_site',
            'mainsite_badgrapp',
        )

        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            [cursor.execute("TRUNCATE TABLE " + table) for table in seed_filled_tables]
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        print("\033[92mdone!\033[0m")