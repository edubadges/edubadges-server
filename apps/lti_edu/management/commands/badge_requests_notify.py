from django.core.management.base import BaseCommand
from lti_edu.models import StudentsEnrolled
from mainsite.utils import EmailMessageMaker
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Notifies users belonging to issuers of new badge requests within last 24 hours'

    def handle(self, *args, **options):
        command_frequency = 500  # hours
        new_enrollments = StudentsEnrolled.objects\
            .filter(date_created__gte=timezone.now()-timedelta(hours=command_frequency))\
            .filter(date_awarded=None)\
            .filter(denied=False)
        staff = StudentsEnrolled.objects.none()  # create empty queryset
        badge_classes = {}
        for enrollment in new_enrollments:
            badge_class = enrollment.badge_class
            try:
                badge_classes[badge_class] += 1
            except KeyError:
                badge_classes[badge_class] = 1
            staff |= badge_class.issuer.staff.all()
        staff = staff.distinct()

        old_unprocessed_enrollments = StudentsEnrolled.objects \
            .filter(date_created__lt=timezone.now() - timedelta(hours=command_frequency)) \
            .filter(date_awarded=None)\
            .filter(denied=False)
        old_badge_classes = {}
        for enrollment in old_unprocessed_enrollments:
            badge_class = enrollment.badge_class
            try:
                old_badge_classes[badge_class] += 1
            except KeyError:
                old_badge_classes[badge_class] = 1

        # filter the results per staff member
        for user in staff:
            badge_classes_new_enrollments = dict((badge_class, counter) for badge_class, counter in badge_classes.iteritems() if user in badge_class.issuer.staff.all())
            badge_classes_old_enrollments = dict((badge_class, counter) for badge_class, counter in old_badge_classes.iteritems() if user in badge_class.issuer.staff.all())
            message = EmailMessageMaker.create_issuer_staff_badge_request_email(badge_classes_new_enrollments,
                                                                                badge_classes_old_enrollments)
            user.email_user(subject='You have badge requests waiting for you.', message=message)
