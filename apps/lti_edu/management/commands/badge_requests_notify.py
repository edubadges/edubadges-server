from django.core.management.base import BaseCommand
from lti_edu.models import StudentsEnrolled
from lti_edu.utils import create_issuer_staff_badge_request_email
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Notifies users belonging to issuers of new badge requests within last 24 hours'

    def handle(self, *args, **options):
        command_frequency = 24  # hours
        new_enrollments = StudentsEnrolled.objects\
            .filter(date_created__gte=timezone.now()-timedelta(hours=command_frequency))\
            .filter(date_awarded=None)

        staff = StudentsEnrolled.objects.none()  # create empty queryset
        badge_classes = []
        for enrollment in new_enrollments:
            badge_class = enrollment.badge_class
            badge_classes.append(badge_class)
            staff |= badge_class.issuer.staff.all()
        staff = staff.distinct()

        for user in staff:
            relevant_badge_classes = [bc for bc in badge_classes if user in bc.issuer.staff.all()]
            message = create_issuer_staff_badge_request_email(relevant_badge_classes)
            user.email_user(subject='You have badge requests waiting for you.', message=message)
