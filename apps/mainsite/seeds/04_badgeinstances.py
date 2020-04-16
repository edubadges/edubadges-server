import uuid

from allauth.socialaccount.models import SocialAccount
from django.conf import settings

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass, BadgeInstance
from lti_edu.models import StudentsEnrolled
from mainsite.models import BadgrApp
from mainsite.seeds.constants import ENROLLED_STUDENT_EMAIL, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY, \
    BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_GROUP_DYNAMICS, BADGE_CLASS_PSYCHOMETRICS

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
badgr_app = BadgrApp.objects.get(id=1)


def create_badge_instance(user, badge_class, revoked):
    social_account = SocialAccount.objects.get(user=user)

    badge_class.issue(recipient_id=social_account.uid, created_by=super_user, allow_uppercase=True,
                      recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID,
                      badgr_app=badgr_app, identifier=uuid.uuid4().urn, revoked=revoked)


# Create enrollments


def create_enrollments_badge_instances(user, bc_names, revoked):
    for bc_name in bc_names:
        for bc in BadgeClass.objects.filter(name=bc_name):
            StudentsEnrolled.objects.get_or_create(badge_class=bc, user=enrolled_user)
            # Create badge instances
            create_badge_instance(user, bc, revoked)


enrolled_user = BadgeUser.objects.get(email=ENROLLED_STUDENT_EMAIL)
create_enrollments_badge_instances(enrolled_user,
                                   [BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY],
                                   False)

create_enrollments_badge_instances(enrolled_user,
                                   [BADGE_CLASS_PSYCHOMETRICS, BADGE_CLASS_GROUP_DYNAMICS],
                                   True)
