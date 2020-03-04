from institution.models import Institution
from badgeuser.models import BadgeUser
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from staff.models import InstitutionStaff


# Institution
[
    Institution(name=ins).save() for ins in [
        'university-example.org',
        'diy.surfconext.nl'
    ]
]


# Users - Teachers
all_perms = {
    'create': True,
    'read': True,
    'update': True,
    'destroy': True,
    'award': True,
    'sign': True,
    'administrate_users': True
}


def create_teacher(username, email, institution_name, uid, perms = all_perms):
    BadgeUser(is_staff=1, username=username, email=email).save()

    user = BadgeUser.objects.get(username=username, email=email)
    EmailAddress(verified=1, primary=1, email=email, user=user).save()
    SocialAccount(provider='surf_conext', uid=uid, user=user).save()

    institution = Institution.objects.get(name=institution_name)
    InstitutionStaff(**perms, user=user, institution=institution).save()


teachers = [
    {
        "username": "joseph+weeler",
        "email": "Joseph+Weeler@university-example.org",
        "institution_name": "university-example.org",
        "uid": "74ea5d1e44a80547db8b0400debb2f340fabd215",
    }
]

[create_teacher(**t) for t in teachers]


# Users - Students
def create_student(username, email, uid):
    BadgeUser(username=username, email=email).save()

    user = BadgeUser.objects.get(username=username, email=email)
    EmailAddress(verified=1, primary=1, email=email, user=user).save()
    SocialAccount(provider='edu_id', uid=uid, user=user).save()


students = [
    {
        "username": "student",
        "email": "student1@diy.surfconext.nl",
        "uid": "urn:mace:eduid.nl:1.0:1befe8a3-94ad-41b3-832a-bcbbe2ddeaaa:c34127f7-0f27-4743-9ffe-7210db55817a"
    }
]

[create_student(**s) for s in students]
