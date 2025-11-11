from cmath import exp
from datetime import timedelta
from venv import logger

from badgeuser.models import BadgeUser, StudentAffiliation
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone
from institution.models import Faculty, Institution
from issuer.models import BadgeClass, BadgeInstance, Issuer
from lti_edu.models import StudentsEnrolled
from mainsite.models import BadgrApp

super_user = BadgeUser.objects.get(username=getattr(settings, 'SUPERUSER_NAME'))

# By default, badge instances expire in 6 months, we will override this per badge instance so several are expired
months_ahead = 6


def all_students_in(institution: Institution) -> QuerySet[BadgeUser]:
    return BadgeUser.objects.filter(
        is_active=True,
        is_superuser=False,
        is_staff=False,
    )


def all_badge_classes_in(institution: Institution) -> QuerySet[BadgeClass]:
    faculties = Faculty.objects.filter(institution=institution)
    issuers = Issuer.objects.filter(faculty__in=faculties)

    return BadgeClass.objects.filter(
        issuer__in=issuers,
        archived=False,
    )


for institution in Institution.objects.all():
    badge_classes = all_badge_classes_in(institution)
    users = all_students_in(institution)

    logger.debug(
        f'Generating {len(users)} x {len(badge_classes)} = {len(users) * len(badge_classes)} badge instances in {institution.name}'
    )

    for index, badge_class in enumerate(badge_classes):
        # Every even badge is accepted, uneven is unaccepted and every 5th is rejected
        if index % 2 == 0:
            acceptance = BadgeInstance.ACCEPTANCE_ACCEPTED
        elif index % 5 == 0:
            acceptance = BadgeInstance.ACCEPTANCE_REJECTED
        else:
            acceptance = BadgeInstance.ACCEPTANCE_UNACCEPTED

        # When we want some revoked badges, here's where to do that
        revoked = False

        # substract a month of expiration for each badge instance
        expires_at = timezone.now() + timedelta(days=months_ahead * 30) - timedelta(days=index * 30)

        for user in users:
            StudentsEnrolled.objects.get_or_create(badge_class=badge_class, user=user)

            badge_class.issue(
                recipient=user,
                created_by=super_user,
                allow_uppercase=True,
                recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                acceptance=acceptance,
                revoked=revoked,
                expires_at=expires_at,
                send_email=False,
                # publish_parent=False
            )
