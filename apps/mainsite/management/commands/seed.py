import sys
import traceback
from os import listdir
from os.path import dirname, isfile, join
from random import randrange

import badgrlog
from badgeuser.models import BadgeUser
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone
from institution.models import Faculty, Institution
from issuer.models import BadgeClass, BadgeInstance, Issuer
from mainsite.models import BadgrApp
from mainsite.tests.base import SetupHelper


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--clean', action='store_true')
        parser.add_argument('-as', '--add_assertions', type=int)
        parser.add_argument('-cf', '--check_first', action='store_true')
        parser.add_argument('--seedbank', required=True, help='Specify the seedbank to use (e.g., proeftuin)')

    def handle(self, *args, **options):
        if not settings.ALLOW_SEEDS:
            print('Not seeding: ALLOW_SEEDS is set to false')
            return

        with override_settings(
            CACHES={
                'default': {
                    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
                }
            }
        ):
            if options['clean']:
                clear_data()

            seeds = get_seeds(options['seedbank'])
            run_seeds(seeds)
            if options['add_assertions']:
                nr_of_assertions = options['add_assertions']
                run_scaled_seed(scale=nr_of_assertions)


def clear_data():
    with connection.cursor() as cursor:
        print('Wiping data... ', end='')

        schema = 'public'
        migration_filled_tables = ('auth_permission', 'django_content_type', 'django_migrations')

        sql = (
            f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}' "
            f"AND table_name NOT IN {migration_filled_tables} AND table_type = 'BASE TABLE'"
        )
        cursor.execute(sql)
        for (table,) in cursor.fetchall():
            cursor.execute(f'TRUNCATE TABLE {schema}.{table} CASCADE')

        print('\033[92mdone!\033[0m')


def get_seeds(seedbank):
    """Get list of seed modules for a given seedbank"""

    ## There is quite probably a much more pythonic way to get a list of python files that are modules.

    seedsdir = join(dirname(__file__), f'../../seeds/{seedbank}')
    seeds = listdir(seedsdir)
    # Filter out anything that is not a file
    seeds = filter(lambda seed: isfile(join(seedsdir, seed)), seeds)
    # Filter out __ini__.py, constants.py, and util.py
    seeds = filter(lambda seed: seed not in ['__init__.py', 'constants.py', 'util.py'], seeds)

    # Filter out anything not ending in .py then remove the extension
    seeds = filter(lambda seed: seed.endswith('.py'), seeds)
    seeds = map(lambda seed: seed.replace('.py', ''), seeds)
    # turn the list of seed names into a list of seed module names return sorted
    seeds = map(lambda seed: f'mainsite.seeds.{seedbank}.{seed}', seeds)
    return sorted(seeds)


def run_seeds(seeds):
    """Run the specified seed modules"""
    for seed in seeds:
        try:
            __import__(seed)
            print('\033[92mdone!\033[0m')
        except Exception as e:
            sys.stderr.write('\033[91mFAILED!\033[0m')
            sys.stderr.write(traceback.format_exc())
            sys.stderr.write(f'{str(e)}\n')
            sys.exit(1)


def run_scaled_seed(scale):
    setup_helper = SetupHelper()
    institution = Institution.objects.get(identifier='SURF')
    faculty_name = 'Many Assertions'
    faculty, _ = Faculty.objects.get_or_create(
        name_english=faculty_name,
        description_english=f'Description for {faculty_name}',
        description_dutch=f'Beschrijving voor {faculty_name}',
        institution=institution,
    )
    issuer_name = 'Many Assertions'
    issuer, _ = Issuer.objects.get_or_create(
        name_english=issuer_name,
        description_english=f'Description for {issuer_name}',
        description_dutch=f'Beschrijving voor {issuer_name}',
        faculty=faculty,
        old_json='{}',
        url_english='https://issuer',
        email='issuer@info.nl',
        image_english=seed_image_for('issuers', 'logo-surf.png'),
    )
    badgeclass, _ = BadgeClass.objects.get_or_create(
        name='Many Assertions',
        issuer=issuer,
        description='Description',
        formal=True,
        old_json='{}',
        image=seed_image_for('badges', 'welcome.png'),
    )

    issuing_teacher = BadgeUser.objects.get(first_name='Joseph', last_name='Wheeler')

    for i in range(scale):
        if i % 50 == 0:
            print('Seeding assertion {} out of {}'.format(i, scale))
        recipient = setup_helper.setup_student(affiliated_institutions=[institution])
        assertion = BadgeInstance.objects.create(
            badgeclass=badgeclass,
            recipient_identifier=recipient.get_recipient_identifier(),
            created_by=issuing_teacher,
            created_at=timezone.now().replace(month=randrange(12) + 1),
            user=recipient,
        )

        # Log the badge instance creation event
        logger = badgrlog.BadgrLogger()
        logger.event(badgrlog.BadgeInstanceCreatedEvent(assertion))
