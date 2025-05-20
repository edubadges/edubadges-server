import datetime
import logging

from django.core.management.base import BaseCommand
from django.db import connections


def _remove_cached_direct_awards(direct_award):
    direct_award.badgeclass.remove_cached_data(
        ['cached_direct_awards', 'cached_pending_direct_awards', 'cached_direct_award_bundles'])
    direct_award.bundle.remove_cached_data(['cached_direct_awards'])


class Command(BaseCommand):
    """A command to delete direct awards with the status Deleted."""

    def handle(self, *args, **kwargs):
        from directaward.models import DirectAward

        # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
        connections.close_all()

        logger = logging.getLogger('Badgr.Debug')
        logger.info("Running delete_direct_awards")

        now = datetime.datetime.now(datetime.timezone.utc)
        direct_awards = DirectAward.objects.filter(delete_at__lt=now,
                                                   status='Deleted').all()

        for direct_award in direct_awards:
            _remove_cached_direct_awards(direct_award)
            direct_award.delete()

        logger.info(f"Deleted {len(direct_awards)} direct_awards")
