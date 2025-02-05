import json
import uuid

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, TermsAgreement, StudentAffiliation
from institution.models import Institution
from mainsite.seeds.constants import ENROLLED_STUDENT_EMAIL, REVOKED_STUDENT_EMAIL, INSTITUTION_UNIVERSITY_EXAMPLE_ORG, \
    AWARDED_STUDENT_EMAIL, DEMO_STUDENT_EMAIL, DEMO_STUDENT_EPPN
from staff.models import InstitutionStaff
from .util import add_terms_institution

# Institution
institutions = [
    {'name_english': INSTITUTION_UNIVERSITY_EXAMPLE_ORG,
     'description_english': 'The university example is always a good place to hang out',
     'description_dutch': 'De university example is altijd een goede plek om rond te hangen (wat een vertaling)',
     'institution_type': 'WO'
     },
    {'name_english': 'diy.surfconext.nl',
     'description_english': 'The university diy is also a good place to hang out',
     'description_dutch': 'De university diy is ook een mooie plek',
     'institution_type': 'HBO'
     },
    {'name_english': 'university1',
     'description_english': 'University1 description',
     'description_dutch': 'University1 beschrijving',
     'institution_type': 'MBO'
     },
    {'name_english': 'university2',
     'description_english': 'University1 description',
     'description_dutch': 'University1 beschrijving',
     'institution_type': 'HBO'
     },
]
for ins in institutions:
    institution, _ = Institution.objects.get_or_create(identifier=ins['name_english'],
                                                       name_english=ins['name_english'],
                                                       description_english=ins['description_english'],
                                                       description_dutch=ins['description_dutch'],
                                                       institution_type=ins['institution_type'],
                                                       image_english="uploads/institution/surf.png",
                                                       image_dutch="uploads/institution/surf.png",
                                                       grading_table="https://url.to.gradingtable/gradingtable.html",
                                                       direct_awarding_enabled=True,
                                                       micro_credentials_enabled=True,
                                                       brin="000-7777-11111")
    add_terms_institution(institution)


def accept_terms(user):
    if user.is_teacher:
        terms = user.institution.cached_terms()
        for term in terms:
            terms_agreement, _ = TermsAgreement.objects.get_or_create(user=user, terms=term)
            terms_agreement.agreed_version = term.version
            terms_agreement.agreed = True
            terms_agreement.save()


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

no_perms = {
    'may_create': False,
    'may_read': False,
    'may_update': False,
    'may_delete': False,
    'may_award': False,
    'may_sign': False,
    'may_administrate_users': False
}


def create_admin(username, email, first_name, last_name, institution_name, uid, perms=all_perms):
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email, last_name=last_name,
                                              first_name=first_name, is_teacher=True, invited=True,
                                              is_superuser=True)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution
    accept_terms(user)
    user.save()
    InstitutionStaff.objects.get_or_create(user=user, institution=institution, **perms)


def create_teacher(username, email, first_name, last_name, institution_name, uid, perms=no_perms):
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email, last_name=last_name,
                                              first_name=first_name, is_teacher=True, invited=True)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution
    accept_terms(user)
    user.save()


institution_admins = [
    # staff1
    {
        "username": "joseph+weeler",
        "email": "Joseph+Weeler@university-example.org",
        "first_name": "Joseph",
        "last_name": "Wheeler",
        "institution_name": "university-example.org",
        "uid": "bf847baedbe7045394ea38de3c994f0332f2dfcb",
    },
    # staff2
    {
        "username": "anthony+west",
        "email": "Anthony_West@university-example.org",
        "first_name": "Anthony",
        "last_name": "West",
        "institution_name": "university-example.org",
        "uid": "b57dc8a602a198b8f75f4a427e0464cd1029869a",
    },
    {
        "username": "test12345",
        "email": "thisisa@valid.email",
        "first_name": "Firster",
        "last_name": "LastNamer",
        "institution_name": "university-example.org",
        "uid": "5d0584e3bf178ab4f6d6c9e02ebbd195afd10853",
    },
    {
        "username": "p1u1",
        "email": "professor1@university1.org",
        "first_name": "professor1",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "a20ccd72975606f20a05772182482b0eeb88dc09",
    },
    {
        "username": "p2u1",
        "email": "professor2@university1.org",
        "first_name": "professor2",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "b40d3e0abe239e22c84605231de16a9ddea9698b",
    },
    {
        "username": "p1u2",
        "email": "professor1@university2.org",
        "first_name": "professor1",
        "last_name": "university2",
        "institution_name": "university2",
        "uid": "00020001",
    },
]

teachers = [
    {
        "username": "test123456",
        "email": "test123456@university-example.org",
        "first_name": "Seconder",
        "last_name": "LastNamer2",
        "institution_name": "university-example.org",
        "uid": "847292f4f83cfc3835d9f367c4ec659a4c844a0a",
    },
    {
        "username": "p3u1",
        "email": "professor3@university1.org",
        "first_name": "professor3",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "e1d42cb2da86d8763053ea7c9e29ad87fcbc73aa",
    },
    {
        "username": "p4u1",
        "email": "professor4@university1.org",
        "first_name": "professor4",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "52622709ca4e5590a611d5f6f49f0712c7e513a8",
    },
    {
        "username": "p5u1",
        "email": "professor5@university1.org",
        "first_name": "professor5",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "aaf4dda63707f0b2a59fdfaee75df0ce7579bbe0",
    },
    {
        "username": "p6u1",
        "email": "professor6@university1.org",
        "first_name": "professor6",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "72ca9407474db806cfb457ac00a12dc601865591",
    },
    {
        "username": "p7u1",
        "email": "professor7@university1.org",
        "first_name": "professor7",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "02ffce96ae4a9c318ae074054429a8fed7784442",
    },
    {
        "username": "p8u1",
        "email": "professor8@university1.org",
        "first_name": "professor8",
        "last_name": "university1",
        "institution_name": "university1",
        "uid": "9a988eab38ad87ee4398e0af6f5807d63255cf6a",
    },
    {
        "username": "p2u2",
        "email": "professor2@university2.org",
        "first_name": "professor2",
        "last_name": "university2",
        "institution_name": "university2",
        "uid": "00020002",
    },
]

[create_admin(**a) for a in institution_admins]

[create_teacher(**t) for t in teachers]

# Users - Students
default_extra_data = {"eduid": str(uuid.uuid4())}

def create_student(username, first_name, last_name, email, uid, **kwargs):
    user, _ = BadgeUser.objects.get_or_create(username=username, email=email, first_name=first_name,
                                              last_name=last_name, validated_name=f"{first_name} {last_name}")
    accept_terms(user)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    social_account, _ = SocialAccount.objects.get_or_create(provider='edu_id', uid=uid, user=user)

    extra_data = default_extra_data | kwargs.get("extra_data", {})
    social_account.extra_data = json.dumps(extra_data)

    if kwargs and kwargs.get("affiliation"):
        StudentAffiliation.objects.get_or_create(user=user, **kwargs["affiliation"])

    social_account.save()

students = [
    {
        "username": "user",
        "first_name": "John",
        "last_name": "Doe",
        "email": "edubadges.surf@gmail.com",
        "uid": "5acb63239f298a0a7de0081cd4a603d807178846"
    },
    {
        "username": "mary",
        "first_name": "Mary",
        "last_name": "Doe",
        "email": ENROLLED_STUDENT_EMAIL,
        "uid": "7ec1acf9ce98835e29c337077491b4ba6d1ed21d"
    },
    {
        "username": "sarah",
        "first_name": "Sarah",
        "last_name": "Weirdćharacter",
        "email": REVOKED_STUDENT_EMAIL,
        "uid": "7fc994786c9e7815da17f5e97f796f67e891509e"
    },
    {
        "username": "carl",
        "first_name": "Carl",
        "last_name": "Doolittle",
        "email": AWARDED_STUDENT_EMAIL,
        "uid": "78b9ec1bb8731ec04b42137faf6a3c7068c89212"
    },
    {
        "username": "petra",
        "first_name": "Petra",
        "last_name": "Penttilä",
        "email": DEMO_STUDENT_EMAIL,
        "uid": "fc4f39e6-b8b5-4af0-a5a1-43d9876503ea",
        "affiliation": {
            "schac_home": "university-example.org",
            "eppn": DEMO_STUDENT_EPPN,
        },
        "extra_data": {
            "eduid": "7bf2c4ae-f355-496d-8bc2-db550f1e2d7a"
        }
    },
]

[create_student(**s) for s in students]
