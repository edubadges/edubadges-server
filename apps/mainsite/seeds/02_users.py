import json
import uuid
import urllib.request
import urllib.error

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, TermsAgreement, StudentAffiliation
from institution.models import Institution
from mainsite.seeds.constants import (
    ENROLLED_STUDENT_EMAIL,
    REVOKED_STUDENT_EMAIL,
    INSTITUTION_UNIVERSITY_EXAMPLE_ORG,
    AWARDED_STUDENT_EMAIL,
    DEMO_STUDENT_EMAIL,
    DEMO_STUDENT_EPPN,
)
from staff.models import InstitutionStaff
from .util import add_terms_institution

# Institution
institutions = [
    {
        'name_english': 'mbob.nl',
        'description_english': 'MBO Beek Institution',
        'description_dutch': 'MBO Beek Instelling',
        'institution_type': 'MBO',
    },
    {
        'name_english': 'uvh.nl',
        'description_english': 'Universiteit van Harderwijk Institution',
        'description_dutch': 'Universiteit van Harderwijk Instelling',
        'institution_type': 'WO',
    },
    {
        'name_english': 'hbot.nl',
        'description_english': 'HBO Thee Institution',
        'description_dutch': 'HBO Thee Instelling',
        'institution_type': 'HBO',
    },
    {
        'name_english': 'tun.nb',
        'description_english': 'Theed University of Naboo Institution',
        'description_dutch': 'Theed University of Naboo Instelling',
        'institution_type': 'WO',
    },
]

# TODO: Need to add images

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
        ob3_ssi_agent_enabled=True,
        brin='000-7777-11111',
    )
    add_terms_institution(institution)


def accept_terms(user):
    # if user.is_teacher:
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
        'email': 'Joseph+Weeler@mbob.nl',
        'first_name': 'Joseph',
        'last_name': 'Wheeler',
        'institution_name': 'mbob.nl',
        'uid': 'bf847baedbe7045394ea38de3c994f0332f2dfcb',
    },
    # professor 1
    {
        'username': 'p1u1',
        'email': 'jordan@uvh.nl',
        'first_name': 'Jordan',
        'last_name': 'Belfort',
        'institution_name': 'uvh.nl',
        'uid': '86877d2f465c7ae597798bd2f929568904af023f',
    },
    # teacher 3
    {
        'username': 'bbernanke',
        'email': 'B.S.Bernanke@hbot.nl',
        'first_name': 'Ben',
        'last_name': 'Bernake',
        'institution_name': 'hbot.nl',
        'uid': '4f516a9d3c32c0a19a4e9fe05b3185feef43a5ae',
    },
]

teachers = [
    # professor 4
    {
        'username': 'g_ohm',
        'email': 'georg.ohm@tun.nb',
        'first_name': 'Georg',
        'last_name': 'Ohm',
        'institution_name': 'tun.nb',
        'uid': 'd2ba7c82a401a4c8f14b53d43af4d6c26712f971',
    },
    # teacher 1
    {
        'username': 'jstiglitz',
        'email': 'Joseph.Stiglitz@uvh.nl',
        'first_name': 'Joseph',
        'last_name': 'Stiglitzller',
        'institution_name': 'uvh.nl',
        'uid': 'f981043d36d8fc3188275cc9fc3bad3ee492ea58',
    },
    # teacher 4
    {
        'username': 'agreenspan',
        'email': 'A.Greenspan@hbot.nl',
        'first_name': 'Alan',
        'last_name': 'Greenspan',
        'institution_name': 'hbot.nl',
        'uid': '72c5c72c5fb00b0718366b45f9fbe14ececd3d6e',
    },
]

[create_admin(**a) for a in institution_admins]

[create_teacher(**t) for t in teachers]

# Users - Students
default_extra_data = {'eduid': str(uuid.uuid4())}


def create_student(username, first_name, last_name, email, uid, **kwargs):
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

    extra_data = default_extra_data | kwargs.get('extra_data', {})
    social_account.extra_data = json.dumps(extra_data)

    if kwargs and kwargs.get('affiliation'):
        StudentAffiliation.objects.get_or_create(user=user, **kwargs['affiliation'])

    social_account.save()


students = [
    {
        'username': 'dhaagen',
        'first_name': 'Dinanda',
        'last_name': 'Haagen',
        'email': 'dhaagen.mbob@dev.eduwallet.nl',
        'uid': '1e0d4b84cebda31915c65935132ee95e3c7801b8914dcf29da27aa4b68198278@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '1e0d4b84cebda31915c65935132ee95e3c7801b8914dcf29da27aa4b68198278@mbob.nl',
        },
        'extra_data': {'eduid': 'f2cb63a9-e044-4ce4-88d1-43202214d915'},
    },
    {
        'username': 'vrijkers',
        'first_name': 'Vibeke',
        'last_name': 'Rijkers',
        'email': 'vrijkers.mbob@dev.eduwallet.nl',
        'uid': 'c621a178896cba11a7664a2f3fe4ad66045a7a780814ccf6b5a41157327e5d9d@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'c621a178896cba11a7664a2f3fe4ad66045a7a780814ccf6b5a41157327e5d9d@mbob.nl',
        },
        'extra_data': {'eduid': '6b1b7217-09f4-4d57-bf64-d8797f5e471f'},
    },
    {
        'username': 'mkuester',
        'first_name': 'Markus',
        'last_name': 'Kuester',
        'email': 'mkuester.mbob@dev.eduwallet.nl',
        'uid': 'a934d085468649b6b625f1fb76fa986d0fbf75925b14449154a1b69927b52a0a@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'a934d085468649b6b625f1fb76fa986d0fbf75925b14449154a1b69927b52a0a@mbob.nl',
        },
        'extra_data': {'eduid': '099c16fc-8262-4dc0-baa5-4bc639aad4ec'},
    },
    {
        'username': 'gbinnendijk',
        'first_name': 'Gloria',
        'last_name': 'Binnendijk',
        'email': 'gbinnendijk.mbob@dev.eduwallet.nl',
        'uid': 'bb360f1378ff324d5026e6498d5e19cc808b4f8bae579e5cf95d040573e69374@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'bb360f1378ff324d5026e6498d5e19cc808b4f8bae579e5cf95d040573e69374@mbob.nl',
        },
        'extra_data': {'eduid': '50d04fe7-89cc-4fa3-84b0-56a806d99e16'},
    },
    {
        'username': 'kroc',
        'first_name': 'Kev',
        'last_name': 'Roc',
        'email': 'kroc.mbob@dev.eduwallet.nl',
        'uid': '6f1bf0eab8f12a18350eb02b1674b7e2d4810b431f94ad2c2a3a6edb079c92af@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '6f1bf0eab8f12a18350eb02b1674b7e2d4810b431f94ad2c2a3a6edb079c92af@mbob.nl',
        },
        'extra_data': {'eduid': '20a817e7-ee71-4794-af45-7045711a69f6'},
    },
    {
        'username': 'ezalcveg',
        'first_name': 'Ehleyr',
        'last_name': 'Zalcveg',
        'email': 'ezalcveg.mbob@dev.eduwallet.nl',
        'uid': 'e2b44b2d9ee30a282c32ed4aaf50d15fc60e990bcf5279ec5e788d1d95152996@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'e2b44b2d9ee30a282c32ed4aaf50d15fc60e990bcf5279ec5e788d1d95152996@mbob.nl',
        },
        'extra_data': {'eduid': '3bc06b53-21b9-4959-8262-6bd866925abc'},
    },
    {
        'username': 'jkurr',
        'first_name': "J'Tali",
        'last_name': 'Kurr',
        'email': 'jkurr.mbob@dev.eduwallet.nl',
        'uid': '542be50096969724421558d29f98c4bfb93bde8e8405770cb5429bbc223a3b14@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '542be50096969724421558d29f98c4bfb93bde8e8405770cb5429bbc223a3b14@mbob.nl',
        },
        'extra_data': {'eduid': '2d052550-355f-4bfe-b7e4-f20bb43198a0'},
    },
    {
        'username': 'avannieuwkerk',
        'first_name': 'Anya',
        'last_name': 'van Nieuwkerk',
        'email': 'avannieuwkerk.mbob@dev.eduwallet.nl',
        'uid': '050a9444d7b063ee226c7a6c2d798ecb1a14e466d9316887dbe9849bcdb1fa8a@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '050a9444d7b063ee226c7a6c2d798ecb1a14e466d9316887dbe9849bcdb1fa8a@mbob.nl',
        },
        'extra_data': {'eduid': 'a0fcd65d-a0ed-4e8f-850a-1ac526258324'},
    },
    {
        'username': 'shankins',
        'first_name': 'Sharon',
        'last_name': 'Hankins',
        'email': 'shankins.mbob@dev.eduwallet.nl',
        'uid': '13b5f8c3fdad43d17b5ca75b05bed169be9294476bbbc2127ff24fa2aaa35286@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '13b5f8c3fdad43d17b5ca75b05bed169be9294476bbbc2127ff24fa2aaa35286@mbob.nl',
        },
        'extra_data': {'eduid': '43e27e05-a688-41df-ab1e-b74271fe02c6'},
    },
    {
        'username': 'lgomezllarnas',
        'first_name': 'Ludovica',
        'last_name': 'Gómez Llarnas',
        'email': 'lgomezllarnas.mbob@dev.eduwallet.nl',
        'uid': '241cb038ceb445919c7934d2a308042fa0894f91f9111c34ef5959c1bec25332@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '241cb038ceb445919c7934d2a308042fa0894f91f9111c34ef5959c1bec25332@mbob.nl',
        },
        'extra_data': {'eduid': '99a43a80-44c9-456c-b9e5-a3b799d96258'},
    },
    {
        'username': 'elamore',
        'first_name': 'Esmee',
        'last_name': 'Lamore',
        'email': 'elamore.mbob@dev.eduwallet.nl',
        'uid': '4c46325a72a22ec51e035678717e2980f3cd36d118fa70c0c3f4a511d54b1333@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '4c46325a72a22ec51e035678717e2980f3cd36d118fa70c0c3f4a511d54b1333@mbob.nl',
        },
        'extra_data': {'eduid': '6bed301f-1be7-4a39-ab6c-fa73769fe179'},
    },
    {
        'username': 'khuisman',
        'first_name': 'Kian',
        'last_name': 'Huisman',
        'email': 'khuisman.mbob@dev.eduwallet.nl',
        'uid': 'ff5fb778854a6a85a425f7ee5445d0e0657257795674404c3b764246b26879fe@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'ff5fb778854a6a85a425f7ee5445d0e0657257795674404c3b764246b26879fe@mbob.nl',
        },
        'extra_data': {'eduid': '65825447-1461-4d49-ba56-95d200ac10fc'},
    },
    {
        'username': 'blagerweij',
        'first_name': 'Bente',
        'last_name': 'Lagerweij',
        'email': 'blagerweij.mbob@dev.eduwallet.nl',
        'uid': '3350254193a4171a931d061eb2a800364f4f8ab3493d1a69adbcb89152bddae7@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '3350254193a4171a931d061eb2a800364f4f8ab3493d1a69adbcb89152bddae7@mbob.nl',
        },
        'extra_data': {'eduid': 'cf59e590-4d8b-433e-944d-33f4e9ca00a4'},
    },
    {
        'username': 'fmatthews',
        'first_name': 'Fay',
        'last_name': 'Matthews',
        'email': 'fmatthews.mbob@dev.eduwallet.nl',
        'uid': 'e796c21188c41c80fedbf0e80223a5ad7bcf81296b9fb6ec5077079a23a84210@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'e796c21188c41c80fedbf0e80223a5ad7bcf81296b9fb6ec5077079a23a84210@mbob.nl',
        },
        'extra_data': {'eduid': 'd62f36f2-2d0e-436e-9e16-fcc1304af514'},
    },
    {
        'username': 'khoppenbrouwer',
        'first_name': 'Kevin',
        'last_name': 'Hoppenbrouwer',
        'email': 'khoppenbrouwer.mbob@dev.eduwallet.nl',
        'uid': 'e22d4b8ee1bd3179304ab9aa5179e2ec7a3d68720f76263e3ee7d2f11f39bf29@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': 'e22d4b8ee1bd3179304ab9aa5179e2ec7a3d68720f76263e3ee7d2f11f39bf29@mbob.nl',
        },
        'extra_data': {'eduid': 'cafc6cf2-f029-49c2-bb11-3f1e8197e081'},
    },
    {
        'username': 'lroosenboom',
        'first_name': 'Linde',
        'last_name': 'Roosenboom',
        'email': 'lroosenboom.mbob@dev.eduwallet.nl',
        'uid': '38f184646a7c2eb0e64e67587cd8654df619ee706f7f259020dd8a706a1991b4@mbob.nl',
        'affiliation': {
            'schac_home': 'mbob.nl',
            'eppn': '38f184646a7c2eb0e64e67587cd8654df619ee706f7f259020dd8a706a1991b4@mbob.nl',
        },
        'extra_data': {'eduid': 'bc6a1cdd-267e-4c22-98f1-0ee7714c14e6'},
    },
    # UVH Students
    {
        'username': 'dhaagen_uvh',
        'first_name': 'Dinanda',
        'last_name': 'Haagen',
        'email': 'dhaagen.uvh@dev.eduwallet.nl',
        'uid': '1a799b89ebb579f5d0b567dbf34bcc103d2195309518c3931c2e0e3c28c8d2fe@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '1a799b89ebb579f5d0b567dbf34bcc103d2195309518c3931c2e0e3c28c8d2fe@uvh.nl',
        },
        'extra_data': {'eduid': 'f2cb63a9-e044-4ce4-88d1-43202214d915'},
    },
    {
        'username': 'vrijkers_uvh',
        'first_name': 'Vibeke',
        'last_name': 'Rijkers',
        'email': 'vrijkers.uvh@dev.eduwallet.nl',
        'uid': '6f935ce1945c8d0a8e0a65a424fbff52f97d4674ff882b3cb5ec97fe9d112d09@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '6f935ce1945c8d0a8e0a65a424fbff52f97d4674ff882b3cb5ec97fe9d112d09@uvh.nl',
        },
        'extra_data': {'eduid': '6b1b7217-09f4-4d57-bf64-d8797f5e471f'},
    },
    {
        'username': 'mkuester_uvh',
        'first_name': 'Markus',
        'last_name': 'Kuester',
        'email': 'mkuester.uvh@dev.eduwallet.nl',
        'uid': 'ceec50b053801beb158c45e3a491e04c16a3dce7aca81c859692cb7be6026739@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'ceec50b053801beb158c45e3a491e04c16a3dce7aca81c859692cb7be6026739@uvh.nl',
        },
        'extra_data': {'eduid': '099c16fc-8262-4dc0-baa5-4bc639aad4ec'},
    },
    {
        'username': 'gbinnendijk_uvh',
        'first_name': 'Gloria',
        'last_name': 'Binnendijk',
        'email': 'gbinnendijk.uvh@dev.eduwallet.nl',
        'uid': '479be4b40446b5c5da8c5b938289ed85fae6bbf7a6d861b35231d2f0bdaf44a9@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '479be4b40446b5c5da8c5b938289ed85fae6bbf7a6d861b35231d2f0bdaf44a9@uvh.nl',
        },
        'extra_data': {'eduid': '50d04fe7-89cc-4fa3-84b0-56a806d99e16'},
    },
    {
        'username': 'kroc_uvh',
        'first_name': 'Kev',
        'last_name': 'Roc',
        'email': 'kroc.uvh@dev.eduwallet.nl',
        'uid': '8a5c13651579e84fe6655163ffbbbfdee2ab37066fd0196f07583763f800e2d7@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '8a5c13651579e84fe6655163ffbbbfdee2ab37066fd0196f07583763f800e2d7@uvh.nl',
        },
        'extra_data': {'eduid': '20a817e7-ee71-4794-af45-7045711a69f6'},
    },
    {
        'username': 'ezalcveg_uvh',
        'first_name': 'Ehleyr',
        'last_name': 'Zalcveg',
        'email': 'ezalcveg.uvh@dev.eduwallet.nl',
        'uid': '6cd8f6646257767c6963031c12c61097ab9612bc01c7427af2dacf8f81961908@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '6cd8f6646257767c6963031c12c61097ab9612bc01c7427af2dacf8f81961908@uvh.nl',
        },
        'extra_data': {'eduid': '3bc06b53-21b9-4959-8262-6bd866925abc'},
    },
    {
        'username': 'jkurr_uvh',
        'first_name': "J'Tali",
        'last_name': 'Kurr',
        'email': 'jkurr.uvh@dev.eduwallet.nl',
        'uid': 'd893e858d2bd7e413ccd15d11c44b17fb07720e7ffa6824628f9ed71d6dcf0d1@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'd893e858d2bd7e413ccd15d11c44b17fb07720e7ffa6824628f9ed71d6dcf0d1@uvh.nl',
        },
        'extra_data': {'eduid': '2d052550-355f-4bfe-b7e4-f20bb43198a0'},
    },
    {
        'username': 'avannieuwkerk_uvh',
        'first_name': 'Anya',
        'last_name': 'van Nieuwkerk',
        'email': 'avannieuwkerk.uvh@dev.eduwallet.nl',
        'uid': '7dae9114a41816e16b0a7366270099d78d84661260e4a47e3b8b06a0dd60c006@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '7dae9114a41816e16b0a7366270099d78d84661260e4a47e3b8b06a0dd60c006@uvh.nl',
        },
        'extra_data': {'eduid': 'a0fcd65d-a0ed-4e8f-850a-1ac526258324'},
    },
    {
        'username': 'shankins_uvh',
        'first_name': 'Sharon',
        'last_name': 'Hankins',
        'email': 'shankins.uvh@dev.eduwallet.nl',
        'uid': 'c711c663e64c8b80e4d69e2332dd47bb6c0947337919cc35e6ac2722dd595865@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'c711c663e64c8b80e4d69e2332dd47bb6c0947337919cc35e6ac2722dd595865@uvh.nl',
        },
        'extra_data': {'eduid': '43e27e05-a688-41df-ab1e-b74271fe02c6'},
    },
    {
        'username': 'lgomezllarnas_uvh',
        'first_name': 'Ludovica',
        'last_name': 'Gómez Llarnas',
        'email': 'lgomezllarnas.uvh@dev.eduwallet.nl',
        'uid': 'b302437a74f5e03d2965ad3d152f418c67089c77b36d59332395a8f580724a99@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'b302437a74f5e03d2965ad3d152f418c67089c77b36d59332395a8f580724a99@uvh.nl',
        },
        'extra_data': {'eduid': '99a43a80-44c9-456c-b9e5-a3b799d96258'},
    },
    {
        'username': 'elamore_uvh',
        'first_name': 'Esmee',
        'last_name': 'Lamore',
        'email': 'elamore.uvh@dev.eduwallet.nl',
        'uid': '2002d5b4f3687607890b9435e63d759150d22ca4a8907afe649bf8bce6485ed9@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '2002d5b4f3687607890b9435e63d759150d22ca4a8907afe649bf8bce6485ed9@uvh.nl',
        },
        'extra_data': {'eduid': '6bed301f-1be7-4a39-ab6c-fa73769fe179'},
    },
    {
        'username': 'khuisman_uvh',
        'first_name': 'Kian',
        'last_name': 'Huisman',
        'email': 'khuisman.uvh@dev.eduwallet.nl',
        'uid': 'bebce06b612e78e54eb1e06339ba02f8bd2ed711e5e71a133e8604c624270e16@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'bebce06b612e78e54eb1e06339ba02f8bd2ed711e5e71a133e8604c624270e16@uvh.nl',
        },
        'extra_data': {'eduid': '65825447-1461-4d49-ba56-95d200ac10fc'},
    },
    {
        'username': 'blagerweij_uvh',
        'first_name': 'Bente',
        'last_name': 'Lagerweij',
        'email': 'blagerweij.uvh@dev.eduwallet.nl',
        'uid': '180fbc5db4afc4a4d6fe438642418552742e2d381ceb8e557e020189f7ffb25a@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '180fbc5db4afc4a4d6fe438642418552742e2d381ceb8e557e020189f7ffb25a@uvh.nl',
        },
        'extra_data': {'eduid': 'cf59e590-4d8b-433e-944d-33f4e9ca00a4'},
    },
    {
        'username': 'fmatthews_uvh',
        'first_name': 'Fay',
        'last_name': 'Matthews',
        'email': 'fmatthews.uvh@dev.eduwallet.nl',
        'uid': '58e86ac00d4ea542f8030d782c4c5ceda86469f8c44cf54976b235daa7dc137e@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '58e86ac00d4ea542f8030d782c4c5ceda86469f8c44cf54976b235daa7dc137e@uvh.nl',
        },
        'extra_data': {'eduid': 'd62f36f2-2d0e-436e-9e16-fcc1304af514'},
    },
    {
        'username': 'khoppenbrouwer_uvh',
        'first_name': 'Kevin',
        'last_name': 'Hoppenbrouwer',
        'email': 'khoppenbrouwer.uvh@dev.eduwallet.nl',
        'uid': '41fb33ec98c18e2bede198a665734d9585d223793d457fa296ec652e6a317944@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': '41fb33ec98c18e2bede198a665734d9585d223793d457fa296ec652e6a317944@uvh.nl',
        },
        'extra_data': {'eduid': 'cafc6cf2-f029-49c2-bb11-3f1e8197e081'},
    },
    {
        'username': 'lroosenboom_uvh',
        'first_name': 'Linde',
        'last_name': 'Roosenboom',
        'email': 'lroosenboom.uvh@dev.eduwallet.nl',
        'uid': 'b600ccc2c24d79047bbe93bd81d3e0a9180c4a538893c8c94d8713f9cd6b6e33@uvh.nl',
        'affiliation': {
            'schac_home': 'uvh.nl',
            'eppn': 'b600ccc2c24d79047bbe93bd81d3e0a9180c4a538893c8c94d8713f9cd6b6e33@uvh.nl',
        },
        'extra_data': {'eduid': 'bc6a1cdd-267e-4c22-98f1-0ee7714c14e6'},
    },
    # HBOT Students
    {
        'username': 'dhaagen_hbot',
        'first_name': 'Dinanda',
        'last_name': 'Haagen',
        'email': 'dhaagen.hbot@dev.eduwallet.nl',
        'uid': '1a799b89ebb579f5d0b567dbf34bcc103d2195309518c3931c2e0e3c28c8d2fe@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '1a799b89ebb579f5d0b567dbf34bcc103d2195309518c3931c2e0e3c28c8d2fe@hbot.nl',
        },
        'extra_data': {'eduid': 'f2cb63a9-e044-4ce4-88d1-43202214d915'},
    },
    {
        'username': 'vrijkers_hbot',
        'first_name': 'Vibeke',
        'last_name': 'Rijkers',
        'email': 'vrijkers.hbot@dev.eduwallet.nl',
        'uid': '6f935ce1945c8d0a8e0a65a424fbff52f97d4674ff882b3cb5ec97fe9d112d09@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '6f935ce1945c8d0a8e0a65a424fbff52f97d4674ff882b3cb5ec97fe9d112d09@hbot.nl',
        },
        'extra_data': {'eduid': '6b1b7217-09f4-4d57-bf64-d8797f5e471f'},
    },
    {
        'username': 'mkuester_hbot',
        'first_name': 'Markus',
        'last_name': 'Kuester',
        'email': 'mkuester.hbot@dev.eduwallet.nl',
        'uid': 'ceec50b053801beb158c45e3a491e04c16a3dce7aca81c859692cb7be6026739@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'ceec50b053801beb158c45e3a491e04c16a3dce7aca81c859692cb7be6026739@hbot.nl',
        },
        'extra_data': {'eduid': '099c16fc-8262-4dc0-baa5-4bc639aad4ec'},
    },
    {
        'username': 'gbinnendijk_hbot',
        'first_name': 'Gloria',
        'last_name': 'Binnendijk',
        'email': 'gbinnendijk.hbot@dev.eduwallet.nl',
        'uid': '479be4b40446b5c5da8c5b938289ed85fae6bbf7a6d861b35231d2f0bdaf44a9@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '479be4b40446b5c5da8c5b938289ed85fae6bbf7a6d861b35231d2f0bdaf44a9@hbot.nl',
        },
        'extra_data': {'eduid': '50d04fe7-89cc-4fa3-84b0-56a806d99e16'},
    },
    {
        'username': 'kroc_hbot',
        'first_name': 'Kev',
        'last_name': 'Roc',
        'email': 'kroc.hbot@dev.eduwallet.nl',
        'uid': '8a5c13651579e84fe6655163ffbbbfdee2ab37066fd0196f07583763f800e2d7@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '8a5c13651579e84fe6655163ffbbbfdee2ab37066fd0196f07583763f800e2d7@hbot.nl',
        },
        'extra_data': {'eduid': '20a817e7-ee71-4794-af45-7045711a69f6'},
    },
    {
        'username': 'ezalcveg_hbot',
        'first_name': 'Ehleyr',
        'last_name': 'Zalcveg',
        'email': 'ezalcveg.hbot@dev.eduwallet.nl',
        'uid': '6cd8f6646257767c6963031c12c61097ab9612bc01c7427af2dacf8f81961908@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '6cd8f6646257767c6963031c12c61097ab9612bc01c7427af2dacf8f81961908@hbot.nl',
        },
        'extra_data': {'eduid': '3bc06b53-21b9-4959-8262-6bd866925abc'},
    },
    {
        'username': 'jkurr_hbot',
        'first_name': "J'Tali",
        'last_name': 'Kurr',
        'email': 'jkurr.hbot@dev.eduwallet.nl',
        'uid': 'd893e858d2bd7e413ccd15d11c44b17fb07720e7ffa6824628f9ed71d6dcf0d1@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'd893e858d2bd7e413ccd15d11c44b17fb07720e7ffa6824628f9ed71d6dcf0d1@hbot.nl',
        },
        'extra_data': {'eduid': '2d052550-355f-4bfe-b7e4-f20bb43198a0'},
    },
    {
        'username': 'avannieuwkerk_hbot',
        'first_name': 'Anya',
        'last_name': 'van Nieuwkerk',
        'email': 'avannieuwkerk.hbot@dev.eduwallet.nl',
        'uid': '7dae9114a41816e16b0a7366270099d78d84661260e4a47e3b8b06a0dd60c006@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '7dae9114a41816e16b0a7366270099d78d84661260e4a47e3b8b06a0dd60c006@hbot.nl',
        },
        'extra_data': {'eduid': 'a0fcd65d-a0ed-4e8f-850a-1ac526258324'},
    },
    {
        'username': 'shankins_hbot',
        'first_name': 'Sharon',
        'last_name': 'Hankins',
        'email': 'shankins.hbot@dev.eduwallet.nl',
        'uid': 'c711c663e64c8b80e4d69e2332dd47bb6c0947337919cc35e6ac2722dd595865@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'c711c663e64c8b80e4d69e2332dd47bb6c0947337919cc35e6ac2722dd595865@hbot.nl',
        },
        'extra_data': {'eduid': '43e27e05-a688-41df-ab1e-b74271fe02c6'},
    },
    {
        'username': 'lgomezllarnas_hbot',
        'first_name': 'Ludovica',
        'last_name': 'Gómez Llarnas',
        'email': 'lgomezllarnas.hbot@dev.eduwallet.nl',
        'uid': 'b302437a74f5e03d2965ad3d152f418c67089c77b36d59332395a8f580724a99@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'b302437a74f5e03d2965ad3d152f418c67089c77b36d59332395a8f580724a99@hbot.nl',
        },
        'extra_data': {'eduid': '99a43a80-44c9-456c-b9e5-a3b799d96258'},
    },
    {
        'username': 'elamore_hbot',
        'first_name': 'Esmee',
        'last_name': 'Lamore',
        'email': 'elamore.hbot@dev.eduwallet.nl',
        'uid': '2002d5b4f3687607890b9435e63d759150d22ca4a8907afe649bf8bce6485ed9@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '2002d5b4f3687607890b9435e63d759150d22ca4a8907afe649bf8bce6485ed9@hbot.nl',
        },
        'extra_data': {'eduid': '6bed301f-1be7-4a39-ab6c-fa73769fe179'},
    },
    {
        'username': 'khuisman_hbot',
        'first_name': 'Kian',
        'last_name': 'Huisman',
        'email': 'khuisman.hbot@dev.eduwallet.nl',
        'uid': 'bebce06b612e78e54eb1e06339ba02f8bd2ed711e5e71a133e8604c624270e16@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'bebce06b612e78e54eb1e06339ba02f8bd2ed711e5e71a133e8604c624270e16@hbot.nl',
        },
        'extra_data': {'eduid': '65825447-1461-4d49-ba56-95d200ac10fc'},
    },
    {
        'username': 'blagerweij_hbot',
        'first_name': 'Bente',
        'last_name': 'Lagerweij',
        'email': 'blagerweij.hbot@dev.eduwallet.nl',
        'uid': '180fbc5db4afc4a4d6fe438642418552742e2d381ceb8e557e020189f7ffb25a@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '180fbc5db4afc4a4d6fe438642418552742e2d381ceb8e557e020189f7ffb25a@hbot.nl',
        },
        'extra_data': {'eduid': 'cf59e590-4d8b-433e-944d-33f4e9ca00a4'},
    },
    {
        'username': 'fmatthews_hbot',
        'first_name': 'Fay',
        'last_name': 'Matthews',
        'email': 'fmatthews.hbot@dev.eduwallet.nl',
        'uid': '58e86ac00d4ea542f8030d782c4c5ceda86469f8c44cf54976b235daa7dc137e@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '58e86ac00d4ea542f8030d782c4c5ceda86469f8c44cf54976b235daa7dc137e@hbot.nl',
        },
        'extra_data': {'eduid': 'd62f36f2-2d0e-436e-9e16-fcc1304af514'},
    },
    {
        'username': 'khoppenbrouwer_hbot',
        'first_name': 'Kevin',
        'last_name': 'Hoppenbrouwer',
        'email': 'khoppenbrouwer.hbot@dev.eduwallet.nl',
        'uid': '41fb33ec98c18e2bede198a665734d9585d223793d457fa296ec652e6a317944@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': '41fb33ec98c18e2bede198a665734d9585d223793d457fa296ec652e6a317944@hbot.nl',
        },
        'extra_data': {'eduid': 'cafc6cf2-f029-49c2-bb11-3f1e8197e081'},
    },
    {
        'username': 'lroosenboom_hbot',
        'first_name': 'Linde',
        'last_name': 'Roosenboom',
        'email': 'lroosenboom.hbot@dev.eduwallet.nl',
        'uid': 'b600ccc2c24d79047bbe93bd81d3e0a9180c4a538893c8c94d8713f9cd6b6e33@hbot.nl',
        'affiliation': {
            'schac_home': 'hbot.nl',
            'eppn': 'b600ccc2c24d79047bbe93bd81d3e0a9180c4a538893c8c94d8713f9cd6b6e33@hbot.nl',
        },
        'extra_data': {'eduid': 'bc6a1cdd-267e-4c22-98f1-0ee7714c14e6'},
    },
    # TUN Students
    {
        'username': 'dhaagen_tun',
        'first_name': 'Dinanda',
        'last_name': 'Haagen',
        'email': 'dhaagen.tun@dev.eduwallet.nl',
        'uid': '2c624232cdd221771294dfbb310aca000a0df6ac8b66b696d90ef06fdefb64a3@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '2c624232cdd221771294dfbb310aca000a0df6ac8b66b696d90ef06fdefb64a3@tun.nb',
        },
        'extra_data': {'eduid': 'f2cb63a9-e044-4ce4-88d1-43202214d915'},
    },
    {
        'username': 'vrijkers_tun',
        'first_name': 'Vibeke',
        'last_name': 'Rijkers',
        'email': 'vrijkers.tun@dev.eduwallet.nl',
        'uid': '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b@tun.nb',
        },
        'extra_data': {'eduid': '6b1b7217-09f4-4d57-bf64-d8797f5e471f'},
    },
    {
        'username': 'mkuester_tun',
        'first_name': 'Markus',
        'last_name': 'Kuester',
        'email': 'mkuester.tun@dev.eduwallet.nl',
        'uid': '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '4e07408562bedb8b60ce05c1decfe3ad16b72230967de01f640b7e4729b49fce@tun.nb',
        },
        'extra_data': {'eduid': '099c16fc-8262-4dc0-baa5-4bc639aad4ec'},
    },
    {
        'username': 'gbinnendijk_tun',
        'first_name': 'Gloria',
        'last_name': 'Binnendijk',
        'email': 'gbinnendijk.tun@dev.eduwallet.nl',
        'uid': '40a01af18892db9ccdce27e7ab1661ece5638fe08520ce814cb03cd629db9c5b@tun.nb',  # UID regenerated to fix duplicate
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '40a01af18892db9ccdce27e7ab1661ece5638fe08520ce814cb03cd629db9c5b@tun.nb',
        },
        'extra_data': {'eduid': '50d04fe7-89cc-4fa3-84b0-56a806d99e16'},
    },
    {
        'username': 'kroc_tun',
        'first_name': 'Kev',
        'last_name': 'Roc',
        'email': 'kroc.tun@dev.eduwallet.nl',
        'uid': 'a5a0b5b44e23435aae211da1a4ecba3647e31bf2a0ae8d94d66cede7fd7e718e@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': 'a5a0b5b44e23435aae211da1a4ecba3647e31bf2a0ae8d94d66cede7fd7e718e@tun.nb',
        },
        'extra_data': {'eduid': '20a817e7-ee71-4794-af45-7045711a69f6'},
    },
    {
        'username': 'ezalcveg_tun',
        'first_name': 'Ehleyr',
        'last_name': 'Zalcveg',
        'email': 'ezalcveg.tun@dev.eduwallet.nl',
        'uid': '8d704365a55805a938e67b3e657ef964101d4cbfbb6a20b5222a05c15c65966a@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '8d704365a55805a938e67b3e657ef964101d4cbfbb6a20b5222a05c15c65966a@tun.nb',
        },
        'extra_data': {'eduid': '3bc06b53-21b9-4959-8262-6bd866925abc'},
    },
    {
        'username': 'jkurr_tun',
        'first_name': "J'Tali",
        'last_name': 'Kurr',
        'email': 'jkurr.tun@dev.eduwallet.nl',
        'uid': '0c52cc06b5844ab47bf78e5107799c32248fe497995f05a0fb35cf709302d21f@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '0c52cc06b5844ab47bf78e5107799c32248fe497995f05a0fb35cf709302d21f@tun.nb',
        },
        'extra_data': {'eduid': '2d052550-355f-4bfe-b7e4-f20bb43198a0'},
    },
    {
        'username': 'avannieuwkerk_tun',
        'first_name': 'Anya',
        'last_name': 'van Nieuwkerk',
        'email': 'avannieuwkerk.tun@dev.eduwallet.nl',
        'uid': '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a@tun.nb',
        },
        'extra_data': {'eduid': 'a0fcd65d-a0ed-4e8f-850a-1ac526258324'},
    },
    {
        'username': 'shankins_tun',
        'first_name': 'Sharon',
        'last_name': 'Hankins',
        'email': 'shankins.tun@dev.eduwallet.nl',
        'uid': 'e7f6c011776e8db7cd330b54174fd76f7d0216b612387a5ffcfb81e6f0919683@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': 'e7f6c011776e8db7cd330b54174fd76f7d0216b612387a5ffcfb81e6f0919683@tun.nb',
        },
        'extra_data': {'eduid': '43e27e05-a688-41df-ab1e-b74271fe02c6'},
    },
    {
        'username': 'lgomezllarnas_tun',
        'first_name': 'Ludovica',
        'last_name': 'Gómez Llarnas',
        'email': 'lgomezllarnas.tun@dev.eduwallet.nl',
        'uid': 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': 'd4735e3a265e16eee03f59718b9b5d03019c07d8b6c51f90da3a666eec13ab35@tun.nb',
        },
        'extra_data': {'eduid': '99a43a80-44c9-456c-b9e5-a3b799d96258'},
    },
    {
        'username': 'elamore_tun',
        'first_name': 'Esmee',
        'last_name': 'Lamore',
        'email': 'elamore.tun@dev.eduwallet.nl',
        'uid': '19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '19581e27de7ced00ff1ce50b2047e7a567c76b1cbaebabe5ef03f7c3017bb5b7@tun.nb',
        },
        'extra_data': {'eduid': '6bed301f-1be7-4a39-ab6c-fa73769fe179'},
    },
    {
        'username': 'khuisman_tun',
        'first_name': 'Kian',
        'last_name': 'Huisman',
        'email': 'khuisman.tun@dev.eduwallet.nl',
        'uid': 'c6cc8639b4f4487389ee4bc9cabcf5fa35c15e9059af9961d6ba8d53616e3333@tun.nb',  # UID regenerated to fix duplicate
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': 'c6cc8639b4f4487389ee4bc9cabcf5fa35c15e9059af9961d6ba8d53616e3333@tun.nb',
        },
        'extra_data': {'eduid': '65825447-1461-4d49-ba56-95d200ac10fc'},
    },
    {
        'username': 'blagerweij_tun',
        'first_name': 'Bente',
        'last_name': 'Lagerweij',
        'email': 'blagerweij.tun@dev.eduwallet.nl',
        'uid': '9233d48db669cfa8fc6431451a16bf581a14ff2e044af5e2a1a5fc1d9bd1619b@tun.nb',  # UID regenerated to fix duplicate
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '9233d48db669cfa8fc6431451a16bf581a14ff2e044af5e2a1a5fc1d9bd1619b@tun.nb',
        },
        'extra_data': {'eduid': 'cf59e590-4d8b-433e-944d-33f4e9ca00a4'},
    },
    {
        'username': 'fmatthews_tun',
        'first_name': 'Fay',
        'last_name': 'Matthews',
        'email': 'fmatthews.tun@dev.eduwallet.nl',
        'uid': '7902699be42c8a8e46fbbb4501726517e86b22c56a189f7625a6da49081b2451@tun.nb',
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '7902699be42c8a8e46fbbb4501726517e86b22c56a189f7625a6da49081b2451@tun.nb',
        },
        'extra_data': {'eduid': 'd62f36f2-2d0e-436e-9e16-fcc1304af514'},
    },
    {
        'username': 'khoppenbrouwer_tun',
        'first_name': 'Kevin',
        'last_name': 'Hoppenbrouwer',
        'email': 'khoppenbrouwer.tun@dev.eduwallet.nl',
        'uid': '43515a0ad540996c1276322501426901e156adfba73c672cbf23fb6bf6e079cc@tun.nb',  # UID regenerated to fix duplicate
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '43515a0ad540996c1276322501426901e156adfba73c672cbf23fb6bf6e079cc@tun.nb',
        },
        'extra_data': {'eduid': 'cafc6cf2-f029-49c2-bb11-3f1e8197e081'},
    },
    {
        'username': 'lroosenboom_tun',
        'first_name': 'Linde',
        'last_name': 'Roosenboom',
        'email': 'lroosenboom.tun@dev.eduwallet.nl',
        'uid': '6534ed7c93d2bd29a3de45acf18b8e3ffa50c3175fd7ceee7acb0a638ab552da@tun.nb',  # UID regenerated to fix duplicate
        'affiliation': {
            'schac_home': 'tun.nb',
            'eppn': '6534ed7c93d2bd29a3de45acf18b8e3ffa50c3175fd7ceee7acb0a638ab552da@tun.nb',
        },
        'extra_data': {'eduid': 'bc6a1cdd-267e-4c22-98f1-0ee7714c14e6'},
    },
]

[create_student(**s) for s in students]


def fetch_json_from_url(url):
    """
    Fetch JSON data from external URL with error handling.

    Args:
        url (str): The URL to fetch JSON data from

    Returns:
        dict or None: Parsed JSON data or None if error occurred
    """
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.URLError as e:
        print(f'Error fetching data from {url}: {e}')
        return None
    except json.JSONDecodeError as e:
        print(f'Error parsing JSON from {url}: {e}')
        return None
    except Exception as e:
        print(f'Unexpected error fetching data from {url}: {e}')
        return None


def extract_student_users_from_json(json_data):
    """
    Extract student users from JSON data based on eduPersonAffiliation.

    Args:
        json_data (dict): JSON data containing user information

    Returns:
        list: List of student user dictionaries formatted for create_student()
    """
    if not json_data or not isinstance(json_data, dict):
        return []

    student_users = []

    # Handle different possible JSON structures
    # Check for users in top-level 'users' key, or in IAM/SIS/HR sections
    all_users = []

    if 'users' in json_data:
        all_users.extend(json_data['users'])

    # Check for users in IAM, SIS, HR sections
    for section in ['IAM', 'SIS', 'HR']:
        if section in json_data and isinstance(json_data[section], list):
            all_users.extend(json_data[section])

    # If no structured users found, assume the whole JSON is user data
    if not all_users and isinstance(json_data, dict) and any(key in json_data for key in ['uid', 'givenName', 'sn']):
        all_users = [json_data]

    for user in all_users:
        if not isinstance(user, dict):
            continue

        # Check if user has student affiliation
        affiliations = user.get('eduPersonAffiliation', [])
        if not isinstance(affiliations, list):
            affiliations = [affiliations] if affiliations else []

        # Look for 'student' in any form within affiliations
        is_student = any('student' in str(aff).lower() for aff in affiliations)

        if is_student:
            # Extract required fields
            username = user.get('uid', '')
            first_name = user.get('givenName', '')
            last_name = user.get('sn', '')
            email = user.get('mail', '')
            eppn = user.get('eduPersonPrincipalName', '')
            schac_home = user.get('schacHomeOrganization', '')
            eduid = user.get('eduid', str(uuid.uuid4()))

            # Skip if essential fields are missing
            if not all([username, first_name, last_name, email, eppn]):
                print(
                    f'Skipping user with missing essential fields: uid={username}, givenName={first_name}, sn={last_name}, mail={email}, eppn={eppn}'
                )
                continue

            student_data = {
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'uid': eppn,
                'affiliation': {
                    'schac_home': schac_home,
                    'eppn': eppn,
                },
                'extra_data': {'eduid': eduid},
            }
            student_users.append(student_data)

    return student_users


def update_seed_data_from_url(url):
    """
    Fetch JSON from URL and create student users dynamically.

    Args:
        url (str): URL to fetch JSON data from

    Returns:
        int: Number of students created
    """
    print(f'Fetching student data from: {url}')
    json_data = fetch_json_from_url(url)

    if not json_data:
        print('Failed to fetch or parse JSON data')
        return 0

    student_users = extract_student_users_from_json(json_data)

    if not student_users:
        print('No student users found in JSON data')
        return 0

    print(f'Found {len(student_users)} student users, creating them...')

    for student in student_users:
        try:
            create_student(**student)
            print(f"Created student: {student['username']} ({student['email']})")
        except Exception as e:
            print(f"Error creating student {student['username']}: {e}")

    return len(student_users)


# Example usage:
# To dynamically update seed data from external JSON sources, use:
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/mbob.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/uvh.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/hbot.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/tun.json')
