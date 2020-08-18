import csv
import io

from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from issuer.models import BadgeInstance
from badgeuser.models import BadgeUser
from datetime import datetime


class Command(BaseCommand):
    """A command to create and send the application report."""

    def handle(self, *args, **kwargs):
        superusers = BadgeUser.objects.filter(is_superuser=True)
        all_assertions = BadgeInstance.objects.all()
        filename = 'edubadges_report_{}.csv'.format(datetime.today().strftime('%Y-%m-%d'))
        report_file = io.StringIO()
        report_writer = csv.writer(report_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        report_writer.writerow(['institution', 'faculty', 'issuer', 'badgeclass', 'revoked', 'formal', 'issued_on'])
        for ass in all_assertions:
            row = [ass.badgeclass.issuer.institution.identifier, ass.badgeclass.issuer.faculty.name, ass.badgeclass.issuer.name, ass.badgeclass.name, ass.revoked, ass.badgeclass.formal, ass.issued_on.strftime('%Y-%m-%d')]
            report_writer.writerow(row)
        body = 'Hi Superuser, \n\n' \
               'In the attached csv file you will find your Edubadges report. \n\n' \
               'Regards \n\n' \
               'The Edubadges team'
        for superuser in superusers:
            email = EmailMessage(subject='Your Edubadges report is here!',
                                 body=body,
                                 to=[superuser.primary_email],
                                 attachments=[(filename, report_file.getvalue(), 'text/csv')])
            email.send()
