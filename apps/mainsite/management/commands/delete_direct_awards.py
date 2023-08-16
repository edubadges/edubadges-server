import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import connections
from django.utils.timezone import make_aware


class Command(BaseCommand):
    """A command to delete direct awards with the status Deleted."""

    def handle(self, *args, **kwargs):
        from directaward.models import DirectAward

        # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
        connections.close_all()

        logger = logging.getLogger('Badgr.Debug')
        logger.info("Running delete_direct_awards")

        direct_awards = DirectAward.objects.filter(delete_at__lt=make_aware(datetime.utcnow()),
                                                   status='Deleted').all()

        for direct_award in direct_awards:
            direct_award.delete()

        logger.info(f"Deleted {len(direct_awards)} direct_awards")
