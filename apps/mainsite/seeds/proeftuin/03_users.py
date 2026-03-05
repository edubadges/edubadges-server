import json

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
from badgeuser.models import BadgeUser, StudentAffiliation
from mainsite.seeds.util import read_seed_jsons


def create_student(username: str, first_name: str, last_name: str, email: str, uid: str, **kwargs):
    user, _ = BadgeUser.objects.get_or_create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        validated_name=f'{first_name} {last_name}',
    )

    EmailAddress.objects.get_or_create(verified=1, primary=1, email=email, user=user)
    social_account, _ = SocialAccount.objects.get_or_create(provider='edu_id', uid=uid, user=user)

    extra_data = kwargs.get('extra_data', {})
    social_account.extra_data = json.dumps(extra_data)

    if kwargs and kwargs.get('affiliation'):
        StudentAffiliation.objects.get_or_create(user=user, **kwargs['affiliation'])

    social_account.save()


all_users = read_seed_jsons('pba_*.json')

# Only entries where affiliation includes "student"
students = [u for u in all_users if 'student' in u['eduPersonAffiliation']]

for student in students:
    create_student(
        username=student['mail'],
        first_name=student['givenName'],
        last_name=student['sn'],
        email=student['mail'],
        uid=student['eduPersonPrincipalName'],
        affiliation={'schac_home': student['schacHomeOrganization'], 'eppn': student['eduPersonPrincipalName']},
    )
