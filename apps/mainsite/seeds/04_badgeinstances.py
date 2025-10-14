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


# Generate badge instances for students
print('Creating badge instances for students...')

# Psychology badge classes
psychology_badges = ['Introduction to Psychology', 'Cognitive Psychology', 'Psychometrics', 'Group Dynamics']

# Political Science badge classes
political_science_badges = [
    'Introduction to Political Science',
    'Law and Politics',
    'History of Political Thought',
    'Research Methods',
]

# Medicine badge classes
medicine_badges = [
    'Growth and Development',
    'Circulation and Breathing',
    'Regulation and Integration',
    'Digestion and Defense',
]

# Get some students from different institutions
students_to_award = [
    # MBO students
    ('dhaagen', psychology_badges[:2], False, 'Accepted'),  # 2 accepted psychology badges
    ('vrijkers', psychology_badges, True, 'Accepted'),  # All psychology badges, but revoked
    ('mkuester', political_science_badges[:3], False, 'Accepted'),  # 3 accepted political science badges
    ('gbinnendijk', medicine_badges[:2], False, 'Unaccepted'),  # 2 unaccepted medicine badges
    ('kroc', psychology_badges, False, 'Accepted'),  # All psychology badges, accepted
    # UVH students
    ('dhaagen_uvh', psychology_badges, False, 'Accepted'),  # All psychology badges
    ('vrijkers_uvh', political_science_badges, False, 'Accepted'),  # All political science badges
    ('mkuester_uvh', medicine_badges[:1], False, 'Unaccepted'),  # 1 unaccepted medicine badge
    ('gbinnendijk_uvh', psychology_badges[:1], False, 'Accepted'),  # 1 accepted psychology badge
    # HBOT students
    ('dhaagen_hbot', medicine_badges, False, 'Accepted'),  # All medicine badges
    ('vrijkers_hbot', psychology_badges[:3], False, 'Unaccepted'),  # 3 unaccepted psychology badges
    ('mkuester_hbot', political_science_badges, False, 'Accepted'),  # All political science badges
    # TUN students
    ('dhaagen_tun', psychology_badges[:2], False, 'Accepted'),  # 2 accepted psychology badges
    ('vrijkers_tun', medicine_badges[:3], False, 'Accepted'),  # 3 accepted medicine badges
]

# Create badge instances for each student
for username, badge_names, revoked, acceptance in students_to_award:
    try:
        user = BadgeUser.objects.get(username=username)
        for bc_name in badge_names:
            for bc in BadgeClass.objects.filter(name=bc_name):
                create_badge_instance(user, bc, revoked, acceptance)
            print(
                f'Created {len(badge_names)} badge instance(s) for {username} (revoked={revoked}, acceptance={acceptance})'
            )
    except BadgeUser.DoesNotExist:
        print(f'Warning: User {username} not found, skipping...')
    except Exception as e:
        print(f'Error creating badge instances for {username}: {e}')

print('Badge instance seeding completed!')
