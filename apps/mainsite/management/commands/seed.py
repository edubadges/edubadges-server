import traceback
import sys
from os import listdir, environ
from os.path import dirname, basename, isfile, join
from django.test.utils import override_settings
from django.utils import timezone
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection
from random import randrange
from badgeuser.models import BadgeUser
from mainsite.seeds.util import seed_image_for
from mainsite.tests.base import SetupHelper
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass, BadgeInstance
import badgrlog


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('-c', '--clean', action='store_true')
        parser.add_argument('-as', '--add_assertions', type=int)

    def handle(self, *args, **options):
        if not settings.ALLOW_SEEDS:
            return
            
        with override_settings(CACHES={
            'default': {
                'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
            }
        }):
            if options['clean']:
                clear_data()

            run_seeds()
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


def run_seeds():
    seedsdir = join(dirname(__file__), '../../seeds')
    seeds = [
        basename(x)[:-3]
        for x in listdir(seedsdir)
        if x.endswith('.py')
        if x not in ['__init__.py', 'constants.py', 'util.py']
        if isfile(join(seedsdir, x))
    ]

    for seed in sorted(seeds):
        print('Seeding %s... ' % seed, end='')

        try:
            __import__('mainsite.seeds.' + seed)
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
