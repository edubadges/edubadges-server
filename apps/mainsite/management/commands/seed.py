import traceback
from os import listdir, environ
from os.path import dirname, basename, isfile, join

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--clean', action="store_true")

    def handle(self, *args, **options):
        if settings.ALLOW_SEEDS:
            if options['clean']:
                clear_data()
            run_seeds()


def clear_data():
    with connection.cursor() as cursor:
        print("Wiping data... ", end="")

        dbname = environ.get("BADGR_DB_NAME")
        migration_filled_tables = ('auth_permission', 'django_content_type', 'django_migrations')
        sql = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dbname}' " \
              f"AND table_name NOT IN {migration_filled_tables}"

        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        try:
            cursor.execute(sql)
            for (table,) in cursor.fetchall():
                cursor.execute("TRUNCATE TABLE " + table)
        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        print("\033[92mdone!\033[0m")


def run_seeds():
    seedsdir = join(dirname(__file__), '../../seeds')
    seeds = [
        basename(x)[:-3]
        for x in listdir(seedsdir)
        if x.endswith(".py")
        if x not in ["__init__.py", "constants.py", "util.py"]
        if isfile(join(seedsdir, x))
    ]

    for seed in sorted(seeds):
        print("Seeding %s... " % seed, end="")

        try:
            __import__("mainsite.seeds." + seed)
            print("\033[92mdone!\033[0m")
        except:
            print("\033[91mFAILED!\033[0m")
            traceback.print_exc()
            break
