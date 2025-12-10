from badgeuser.models import UserProvisionment
from django.contrib.contenttypes.models import ContentType
from mainsite.seeds.util import institution_by_identifier, read_seed_jsons

# Load CSV
all_users = read_seed_jsons('pba_*.json')

staff = [u for u in all_users if 'employee' in u['eduPersonAffiliation']]

for member in staff:
    content_type = ContentType.objects.get(model='institution')
    institution = institution_by_identifier(member['schacHomeOrganization'])

    UserProvisionment.objects.get_or_create(
        email=member['mail'],
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
