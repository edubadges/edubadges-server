from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser
from institution.models import Institution
from staff.models import InstitutionStaff

# Institution
[
    Institution.objects.get_or_create(identifier=ins['name'],
                                      name=ins['name'],
                                      description=ins['description'],
                                      image="uploads/institution/surf.png",
                                      grading_table="https://url.to.gradingtable/gradingtable.html",
                                      brin="000-7777-11111") for ins in
    [{'name': 'university-example.org', 'description': 'The university example is always a good place to hang out'},
     {'name': 'diy.surfconext.nl', 'description': 'The university diy is also a good place to hang out'},
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


def create_teacher(username, email, first_name, last_name, institution_name, uid, perms=all_perms):
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email, last_name=last_name,
                                              first_name=first_name)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(name=institution_name)
    user.institution = institution
    InstitutionStaff.objects.filter(user=user, institution=institution).update(**perms)


teachers = [
    {
        "username": "joseph+weeler",
        "email": "Joseph+Weeler@university-example.org",
        "first_name": "Joseph",
        "last_name": "Wheeler",
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
