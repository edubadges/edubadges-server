import json

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, TermsAgreement
from institution.models import Institution
from mainsite.seeds.constants import ENROLLED_STUDENT_EMAIL, REVOKED_STUDENT_EMAIL, INSTITUTION_UNIVERSITY_EXAMPLE_ORG, \
    AWARDED_STUDENT_EMAIL
from staff.models import InstitutionStaff

# Institution
[
    Institution.objects.get_or_create(identifier=ins['name'],
                                      name=ins['name'],
                                      description=ins['description'],
                                      image="uploads/institution/surf.png",
                                      grading_table="https://url.to.gradingtable/gradingtable.html",
                                      brin="000-7777-11111") for ins in
    [{'name': INSTITUTION_UNIVERSITY_EXAMPLE_ORG, 'description': 'The university example is always a good place to hang out'},
     {'name': 'diy.surfconext.nl', 'description': 'The university diy is also a good place to hang out'},
     ]
]


def accept_terms(user):
    TermsAgreement.objects.get_or_create(user=user, terms_version=1, agreed=True, valid=True)


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
                                              first_name=first_name, is_teacher=True)
    accept_terms(user)

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

extra_data = json.dumps({"eduperson_entitlement": ["urn:mace:eduid.nl:entitlement:verified-by-institution"]})


# Users - Students
def create_student(username, email, uid, verify):
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email)
    accept_terms(user)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='edu_id', uid=uid, user=user,
                                        extra_data=extra_data if verify else '{}')


students = [
    {
        "username": "user",
        "first_name" : "John",
        "last_name" : "Doe",
        "email": "edubadges.surf@gmail.com",
        "uid": "5acb63239f298a0a7de0081cd4a603d807178846",
        "verify": True
    },
    {
        "username": "mary",
        "first_name" : "Mary",
        "last_name" : "Doe",
        "email": ENROLLED_STUDENT_EMAIL,
        "uid": "7ec1acf9ce98835e29c337077491b4ba6d1ed21d",
        "verify": True
    },
    {
        "username": "sarah",
        "first_name" : "Sarah",
        "last_name" : "Doe",
        "email": REVOKED_STUDENT_EMAIL,
        "uid": "7fc994786c9e7815da17f5e97f796f67e891509e",
        "verify": True
    },
    {
        "username": "carl",
        "first_name" : "Carl",
        "last_name" : "Doolittle",
        "email": AWARDED_STUDENT_EMAIL,
        "uid": "78b9ec1bb8731ec04b42137faf6a3c7068c89212",
        "verify": True
    }
]

[create_student(**s) for s in students]
