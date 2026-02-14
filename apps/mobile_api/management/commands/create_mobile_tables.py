from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Create mobile API database tables if they do not exist'

    def handle(self, *args, **options):
        try:
            # Get the mobile_api config
            mobile_api_config = apps.get_app_config('mobile_api')

            # Import models to trigger table creation
            from mobile_api.models import MobileDevice, MobileAPIRequestLog

            # Check if tables exist
            with connection.cursor() as cursor:
                # SQLite
                if connection.vendor == 'sqlite':
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND 
                        name IN ('mobile_api_mobiledevice', 'mobile_api_mobileapirequestlog')
                    """)
                # MySQL
                elif connection.vendor == 'mysql':
                    cursor.execute("""
                        SHOW TABLES LIKE 'mobile_api_mobiledevice'
                    """)
                    cursor.execute("""
                        SHOW TABLES LIKE 'mobile_api_mobileapirequestlog'
                    """)
                # PostgreSQL
                elif connection.vendor == 'postgresql':
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' AND 
                        table_name IN ('mobile_api_mobiledevice', 'mobile_api_mobileapirequestlog')
                    """)

                existing_tables = [row[0] for row in cursor.fetchall()]

            if len(existing_tables) >= 2:
                self.stdout.write(self.style.SUCCESS('Mobile API tables already exist'))
            else:
                # Create migrations and migrate
                self.stdout.write('Creating mobile API database tables...')
                from django.core.management import call_command

                call_command('makemigrations', 'mobile_api', '--noinput', verbosity=0)
                call_command('migrate', 'mobile_api', '--noinput', verbosity=1)
                self.stdout.write(self.style.SUCCESS('Successfully created mobile API tables'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating tables: {e}'))
