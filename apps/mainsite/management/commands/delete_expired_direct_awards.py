import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    """A command to create and send the application report."""

    def handle(self, *args, **kwargs):
        from directaward.models import DirectAward
        from mainsite.utils import EmailMessageMaker
        from mainsite.utils import send_mail

        # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
        connections.close_all()

        logger = logging.getLogger('Badgr.Debug')
        logger.info("Running expired_direct_awards")

        two_weeks_ago = datetime.utcnow() - timedelta(days=settings.EXPIRY_DIRECT_AWARDS_WARNING_THRESHOLD_DAYS)
        direct_awards = DirectAward.objects.filter(created_at__lt=two_weeks_ago,
                                                   warning_email_send=False,
                                                   status='Unaccepted').all()

        logger.info(f"Sending {len(direct_awards)} warning_direct_awards reminder emails")

        for direct_award in direct_awards:
            html_message = EmailMessageMaker.direct_award_reminder_student_mail(direct_award)
            direct_award.warning_email_send = True
            direct_award.save()
            send_mail(subject='Reminder: your edubadge will expire',
                      message=None, html_message=html_message, recipient_list=[direct_award.recipient_email])

        half_year_ago = datetime.utcnow() - timedelta(days=settings.EXPIRY_DIRECT_AWARDS_DELETION_THRESHOLD_DAYS)
        direct_awards = DirectAward.objects.filter(created_at__lt=half_year_ago, status='Unaccepted').all()

        logger.info(f"Deleting {len(direct_awards)} expired_direct_awards")

        for direct_award in direct_awards:
            html_message = EmailMessageMaker.direct_award_expired_student_mail(direct_award)
            direct_award.delete()
            send_mail(subject='Your edubadge has been deleted',
                      message=None, html_message=html_message, recipient_list=[direct_award.recipient_email])

        self.stdout.write(f"Direct awards {len(direct_awards)} deleted!\n")
