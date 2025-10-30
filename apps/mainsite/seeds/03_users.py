import json
import uuid
import urllib.request
import urllib.error

from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount

from badgeuser.models import BadgeUser, StudentAffiliation
from institution.models import Institution

from mainsite.seeds.util import read_seed_csv, reformat_email

# Users - Students
default_extra_data = {'eduid': str(uuid.uuid4())}


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

    extra_data = default_extra_data | kwargs.get('extra_data', {})
    social_account.extra_data = json.dumps(extra_data)

    if kwargs and kwargs.get('affiliation'):
        StudentAffiliation.objects.get_or_create(user=user, **kwargs['affiliation'])

    social_account.save()


all_users = read_seed_csv('pba')
# Filter on Profession is "Student"
csv_students = [u for u in all_users if u['Profession'] == 'Student']

institution_shac_homes = Institution.objects.all().values_list('identifier', flat=True)

for student_row in csv_students:
    for shac_home in institution_shac_homes:
        if not shac_home:
            continue
            
        institution_code = shac_home.split('.')[0]
        email = reformat_email(student_row['EmailAddress'], institution_code)
        username = f'{student_row["NonDiacriticalName"]}.{institution_code}'
        global_uuid = f'{student_row["UUID"]}@{shac_home}'

        create_student(
            username=username,
            first_name=student_row['GivenName'],
            last_name=student_row['Surname'],
            email=email,
            uid=global_uuid,
            affiliation={'schac_home': shac_home, 'eppn': f'{student_row["UUID"]}@{shac_home}'},
            extra_data={'eduid': student_row['eduID']},
        )


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

    # TODO: replace with mechanism to run via CSV files

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
            print(f'Created student: {student["username"]} ({student["email"]})')
        except Exception as e:
            print(f'Error creating student {student["username"]}: {e}')

    return len(student_users)


# Example usage:
# To dynamically update seed data from external JSON sources, use:
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/mbob.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/uvh.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/hbot.json')
# update_seed_data_from_url('https://pba.playground.sdp.surf.nl/tun.json')
