from django.contrib.contenttypes.models import ContentType

from badgeuser.models import UserProvisionment
from mainsite.seeds.util import institution_by_shortcode, read_seed_csv, reformat_email

# Load CSV
all_users = read_seed_csv('pba')

# filter on Profession is "Lecturer", "Staff" or "Professor"
professions = ['Lecturer', 'Staff', 'Professor']
staff = [u for u in all_users if u['Profession'] in professions]

for member in staff:
    content_type = ContentType.objects.get(model='institution')
    shortcode = member['Institution'].lower()
    institution = institution_by_shortcode(shortcode)

    email = reformat_email(member['EmailAddress'], shortcode)

    UserProvisionment.objects.get_or_create(
        email=email,
        defaults={
            'content_type': content_type,
            'object_id': institution.id,
            'for_teacher': True,
            'rejected': False,
            'data': {
                'may_create': 1,
                'may_read': 1,
                'may_update': 1,
                'may_delete': 1,
                'may_sign': 1,
                'may_award': 1,
                'may_administrate_users': 1,
            },
        },
    )
