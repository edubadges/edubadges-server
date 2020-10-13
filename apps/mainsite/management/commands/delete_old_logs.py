import os

from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Command that checks the creation date of all the logs and removes the ones older than
    the amount of days set in LOG_STORAGE_DURATION.
    """

    def handle(self, *args, **options):
        log_files = os.listdir(settings.LOGS_DIR)
        for log_file in log_files:
            filename = os.path.join(settings.LOGS_DIR, log_file)
            timestamp = os.path.getmtime(filename)
            date_created = datetime.fromtimestamp(timestamp)
            timedelta_difference = datetime.today() - date_created
            if timedelta_difference.days >= settings.LOG_STORAGE_DURATION:
                os.remove(filename)
