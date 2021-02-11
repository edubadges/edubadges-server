from django.core.mail import EmailMessage
from django.core.management.base import BaseCommand
from django.conf import settings
from institution.models import Institution
from datetime import datetime
import pandas


class Command(BaseCommand):
    """A command to create and send the application report."""

    def handle(self, *args, **kwargs):
        institutions = Institution.objects.all()
        reports = []
        for institution in institutions:
            all_institution_entities = institution.get_all_entities_in_branch()
            for entity in all_institution_entities:
                report = {'institution': institution.name}
                report.update(entity.get_report())
                reports.append(report)
        report = pandas.DataFrame(reports)
        csv_string = report.to_csv(sep=',')
        filename = 'edubadges_report_{}.csv'.format(datetime.today().strftime('%Y-%m-%d'))
        body = 'Dear sir/madam, \n\n' \
               'In the attached csv file you will find your Edubadges report. \n\n' \
               'Regards \n\n' \
               'The Edubadges team'
        if settings.REPORT_RECEIVER_EMAIL:
            email = EmailMessage(subject='Your Edubadges report is here!',
                                 body=body,
                                 to=[settings.REPORT_RECEIVER_EMAIL],
                                 # attachments=[(filename, report_file.getvalue(), 'text/csv')])
                                 attachments=[(filename, csv_string, 'text/csv')])
            email.send()
