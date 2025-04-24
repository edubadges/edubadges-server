import logging
import datetime

from mainsite import settings
from django.core.management.base import BaseCommand
from django.db import connections


def _remove_cached_direct_awards(direct_award):
    direct_award.badgeclass.remove_cached_data(
        ['cached_direct_awards', 'cached_pending_direct_awards', 'cached_direct_award_bundles'])
    direct_award.bundle.remove_cached_data(['cached_direct_awards'])


class Command(BaseCommand):
    """A command to send reminders for unclaimed and open direct awards."""

    def handle(self, *args, **kwargs):
        from directaward.models import DirectAward
        from mainsite.utils import EmailMessageMaker
        from mainsite.utils import send_mail

        # Prevent MySQLdb._exceptions.OperationalError: (2006, 'MySQL server has gone away')
        connections.close_all()

        logger = logging.getLogger('Badgr.Debug')
        logger.info("Running reminders_direct_awards")

        now = datetime.datetime.now(datetime.timezone.utc)

        # We store the reminder number (first reminders sent = 1) to ensure we don't spam the user
        threshold_days = settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS.split(",")
        threshold_days = [int(days.strip()) for days in threshold_days]
        # We need to process them in reverse order
        threshold_days.sort(reverse=True)
        index = len(threshold_days) - 1
        unaccepted = 'Unaccepted'
        for days in threshold_days:
            reminder_date = now - datetime.timedelta(days=days)
            direct_awards = DirectAward.objects.filter(created_at__lt=reminder_date,
                                                       reminders=index,
                                                       expiration_date__isnull=False,
                                                       status=unaccepted).all()
            logger.info(f"Sending {len(direct_awards)} reminder emails for reminder: {index}, threshold: {days}")

            for direct_award in direct_awards:
                html_message = EmailMessageMaker.direct_award_reminder_student_mail(direct_award)
                direct_award.reminders = index + 1
                _remove_cached_direct_awards(direct_award)
                direct_award.save()
                send_mail(subject='Reminder: your edubadge will expire',
                          message=None,
                          html_message=html_message,
                          recipient_list=[direct_award.recipient_email])
            index -= 1

        direct_awards = DirectAward.objects.filter(expiration_date__lt=now,
                                                   status=unaccepted).all()

        logger.info(f"Deleting {len(direct_awards)} expired direct_awards")

        for direct_award in direct_awards:
            html_message = EmailMessageMaker.direct_award_expired_student_mail(direct_award)
            _remove_cached_direct_awards(direct_award)
            direct_award.delete()
            send_mail(subject='Your edubadge has been deleted',
                      message=None,
                      html_message=html_message,
                      recipient_list=[direct_award.recipient_email])

        self.stdout.write(f"Direct awards {len(direct_awards)} deleted!\n")

