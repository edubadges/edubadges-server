from django.conf import settings

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass, BadgeInstance
from lti_edu.models import StudentsEnrolled
from mainsite.models import BadgrApp


super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
badgr_app = BadgrApp.objects.get(id=getattr(settings, 'BADGR_APP_ID'))


def create_badge_instance(user, badge_class, revoked, acceptance='Unaccepted'):
    badge_class.issue(
        recipient=user,
        created_by=super_user,
        allow_uppercase=True,
        recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
        acceptance=acceptance,
        revoked=revoked,
        send_email=False,
    )


def create_enrollments_badge_instances(user, bc_names, revoked, acceptance='Unaccepted', include_badge_instances=True):
    for bc_name in bc_names:
        for bc in BadgeClass.objects.filter(name=bc_name):
            StudentsEnrolled.objects.get_or_create(badge_class=bc, user=user)
            if include_badge_instances:
                create_badge_instance(user, bc, revoked, acceptance)
