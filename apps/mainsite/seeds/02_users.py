import json
import uuid

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, TermsAgreement
from institution.models import Institution
from mainsite.seeds.constants import (
    ENROLLED_STUDENT_EMAIL,
    REVOKED_STUDENT_EMAIL,
    INSTITUTION_UNIVERSITY_EXAMPLE_ORG,
    AWARDED_STUDENT_EMAIL,
)
from staff.models import InstitutionStaff
from .util import add_terms_institution

# Institution
institutions = [
    {
        'name_english': INSTITUTION_UNIVERSITY_EXAMPLE_ORG,
        'description_english': 'The university example is always a good place to hang out',
        'description_dutch': 'De university example is altijd een goede plek om rond te hangen (wat een vertaling)',
        'institution_type': 'WO',
    },
    {
        'name_english': 'harvard-example.edu',
        'description_english': 'Harward Example',
        'description_dutch': 'Hardward Example',
        'institution_type': 'MBO',
    },
    {
        'name_english': 'yale-uni-example.edu',
        'description_english': 'Yale Uni Example',
        'description_dutch': 'Yale Uni Example',
        'institution_type': 'HBO',
    },
]

for ins in institutions:
    institution, _ = Institution.objects.get_or_create(
        identifier=ins['name_english'],
        name_english=ins['name_english'],
        description_english=ins['description_english'],
        description_dutch=ins['description_dutch'],
        institution_type=ins['institution_type'],
        image_english='uploads/institution/surf.png',
        image_dutch='uploads/institution/surf.png',
        grading_table='https://url.to.gradingtable/gradingtable.html',
        direct_awarding_enabled=True,
        micro_credentials_enabled=True,
        brin='000-7777-11111',
    )
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
    'may_administrate_users': True,
}

no_perms = {
    'may_create': False,
    'may_read': False,
    'may_update': False,
    'may_delete': False,
    'may_award': False,
    'may_sign': False,
    'may_administrate_users': False,
}


def create_admin(username, email, first_name, last_name, institution_name, uid, perms=all_perms):
    user, _ = BadgeUser.objects.get_or_create(
        username=username,
        email=email,
        last_name=last_name,
        first_name=first_name,
        is_teacher=True,
        invited=True,
        is_superuser=True,
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution
    accept_terms(user)
    user.save()
    InstitutionStaff.objects.get_or_create(user=user, institution=institution, **perms)


def create_teacher(username, email, first_name, last_name, institution_name, uid, perms=no_perms):
    user, _ = BadgeUser.objects.get_or_create(
        username=username, email=email, last_name=last_name, first_name=first_name, is_teacher=True, invited=True
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    SocialAccount.objects.get_or_create(provider='surf_conext', uid=uid, user=user)

    institution = Institution.objects.get(identifier=institution_name)
    user.institution = institution
    accept_terms(user)
    user.save()


institution_admins = [
    # staff1
    {
        'username': 'joseph+weeler',
        'email': 'Joseph+Weeler@university-example.org',
        'first_name': 'Joseph',
        'last_name': 'Wheeler',
        'institution_name': 'university-example.org',
        'uid': 'bf847baedbe7045394ea38de3c994f0332f2dfcb',
    },
    # professor 1
    {
        'username': 'p1u1',
        'email': 'jordan@harvard-example.edu',
        'first_name': 'Jordan',
        'last_name': 'Belfort',
        'institution_name': 'harvard-example.edu',
        'uid': '86877d2f465c7ae597798bd2f929568904af023f',
    },
    # teacher 3
    {
        'username': 'bbernanke',
        'email': 'B.S.Bernanke@yale-uni-example.edu',
        'first_name': 'Ben',
        'last_name': 'Bernake',
        'institution_name': 'yale-uni-example.edu',
        'uid': '4f516a9d3c32c0a19a4e9fe05b3185feef43a5ae',
    },
]

teachers = [
    # professor 4
    {
        'username': 'g_ohm',
        'email': 'georg.ohm@university-example.org',
        'first_name': 'Georg',
        'last_name': 'Ohm',
        'institution_name': 'university-example.org',
        'uid': 'd2ba7c82a401a4c8f14b53d43af4d6c26712f971',
    },
    # teacher 1
    {
        'username': 'jstiglitz',
        'email': 'Joseph.Stiglitz@harvard-example.edu',
        'first_name': 'Joseph',
        'last_name': 'Stiglitzller',
        'institution_name': 'harvard-example.edu',
        'uid': 'f981043d36d8fc3188275cc9fc3bad3ee492ea58',
    },
    # teacher 4
    {
        'username': 'agreenspan',
        'email': 'A.Greenspan@yale-uni-example.edu',
        'first_name': 'Alan',
        'last_name': 'Greenspan',
        'institution_name': 'yale-uni-example.edu',
        'uid': '72c5c72c5fb00b0718366b45f9fbe14ececd3d6e',
    },
]

[create_admin(**a) for a in institution_admins]

[create_teacher(**t) for t in teachers]

# Users - Students
extra_data = json.dumps({'eduid': str(uuid.uuid4())})


def create_student(username, first_name, last_name, email, uid):
    user, _ = BadgeUser.objects.get_or_create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        validated_name=f'{first_name} {last_name}',
    )
    accept_terms(user)

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    social_account, _ = SocialAccount.objects.get_or_create(provider='edu_id', uid=uid, user=user)
    social_account.extra_data = extra_data
    social_account.save()


students = [
    {
        'username': 'user',
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'edubadges.surf@gmail.com',
        'uid': '5acb63239f298a0a7de0081cd4a603d807178846',
    },
    {
        'username': 'mary',
        'first_name': 'Mary',
        'last_name': 'Doe',
        'email': ENROLLED_STUDENT_EMAIL,
        'uid': '7ec1acf9ce98835e29c337077491b4ba6d1ed21d',
    },
    {
        'username': 'sarah',
        'first_name': 'Sarah',
        'last_name': 'Weirdćharacter',
        'email': REVOKED_STUDENT_EMAIL,
        'uid': '7fc994786c9e7815da17f5e97f796f67e891509e',
    },
    {
        'username': 'carl',
        'first_name': 'Carl',
        'last_name': 'Doolittle',
        'email': AWARDED_STUDENT_EMAIL,
        'uid': '78b9ec1bb8731ec04b42137faf6a3c7068c89212',
    },
]

[create_student(**s) for s in students]
