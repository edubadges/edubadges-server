from institution.models import Institution
from badgeuser.models import BadgeUser
from allauth.socialaccount.models import SocialAccount
from allauth.account.models import EmailAddress
from staff.models import InstitutionStaff


# Institution
[
    Institution.objects.get_or_create(name=ins) for ins in [
        'university-example.org',
        'diy.surfconext.nl'
    ]
]


# Users - Teachers
all_perms = {
    'may_create': True,
    'may_read': True,
    'may_update': True,
    'may_delete': True,
    'may_award': True,
    'may_sign': True,
    'may_administrate_users': True
}


def create_teacher(username, email, institution_name, uid, perms = all_perms):
    user, _ = BadgeUser.objects.get_or_create(is_staff=1, username=username, email=email)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(name=institution_name)
    user.institution = institution
    InstitutionStaff.objects.filter(user=user, institution=institution).update(**perms)


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
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email)
    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='edu_id', uid=uid, user=user)


students = [
    {
        "username": "student",
        "email": "student1@diy.surfconext.nl",
        "uid": "urn:mace:eduid.nl:1.0:1befe8a3-94ad-41b3-832a-bcbbe2ddeaaa:c34127f7-0f27-4743-9ffe-7210db55817a"
    }
]

[create_student(**s) for s in students]
