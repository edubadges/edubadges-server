import sys
from django.conf import settings

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass, BadgeInstance
from lti_edu.models import StudentsEnrolled
from mainsite.models import BadgrApp
from mainsite.seeds.constants import ENROLLED_STUDENT_EMAIL, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY, \
    BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_GROUP_DYNAMICS, BADGE_CLASS_PSYCHOMETRICS, AWARDED_STUDENT_EMAIL, \
    REVOKED_STUDENT_EMAIL, DEMO_STUDENT_EMAIL
from django.conf import settings

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass, BadgeInstance
from lti_edu.models import StudentsEnrolled
from mainsite.models import BadgrApp
from mainsite.seeds.constants import ENROLLED_STUDENT_EMAIL, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY, \
    BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_GROUP_DYNAMICS, BADGE_CLASS_PSYCHOMETRICS, AWARDED_STUDENT_EMAIL, \
    REVOKED_STUDENT_EMAIL

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
badgr_app = BadgrApp.objects.first()
if not badgr_app:
    sys.stderr.write("No BadgrApp found. Did other seeds fail to run?")
    sys.exit(1)

def create_badge_instance(user, badge_class, revoked, acceptance="Unaccepted"):
    badge_class.issue(recipient=user, created_by=super_user, allow_uppercase=True,
                      recipient_type=BadgeInstance.RECIPIENT_TYPE_EDUID, acceptance=acceptance, revoked=revoked,
                      send_email=False)

def create_enrollments_badge_instances(user, bc_names, revoked, acceptance="Unaccepted", include_badge_instances=True):
    for bc_name in bc_names:
        for bc in BadgeClass.objects.filter(name=bc_name):
            StudentsEnrolled.objects.get_or_create(badge_class=bc, user=user)
            if include_badge_instances:
                create_badge_instance(user, bc, revoked, acceptance)

# Create enrollments
demo_user = BadgeUser.objects.get(email=DEMO_STUDENT_EMAIL)
create_enrollments_badge_instances(demo_user,
                                   [BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY],
                                   False,
                                   acceptance="Accepted",
                                   include_badge_instances=True)
create_enrollments_badge_instances(demo_user,
                                   [BADGE_CLASS_GROUP_DYNAMICS, BADGE_CLASS_PSYCHOMETRICS],
                                   False,
                                   acceptance="Unaccepted",
                                   include_badge_instances=True)
create_badge_instance(demo_user, BadgeClass.objects.get(name=settings.EDUID_BADGE_CLASS_NAME), False, "Unaccepted")

enrolled_user = BadgeUser.objects.get(email=ENROLLED_STUDENT_EMAIL)
create_enrollments_badge_instances(enrolled_user,
                                   [BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY,
                                    BADGE_CLASS_GROUP_DYNAMICS],
                                   False,
                                   include_badge_instances=False)

revoked_user = BadgeUser.objects.get(email=REVOKED_STUDENT_EMAIL)
create_enrollments_badge_instances(revoked_user,
                                   [BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_PSYCHOMETRICS,
                                    BADGE_CLASS_GROUP_DYNAMICS],
                                   True,
                                   acceptance="Rejected")

awarded_user = BadgeUser.objects.get(email=AWARDED_STUDENT_EMAIL)
create_enrollments_badge_instances(awarded_user,
                                   [BADGE_CLASS_COGNITIVE_PSYCHOLOGY, BADGE_CLASS_INTRODUCTION_TO_PSYCHOLOGY,
                                    BADGE_CLASS_GROUP_DYNAMICS],
                                   False,
                                   acceptance="Accepted")
