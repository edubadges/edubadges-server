from django.contrib.contenttypes.models import ContentType

from badgeuser.models import UserProvisionment
from mainsite.seeds.util import institution_by_shortcode, read_seed_csv


def reformat_email(email: str, institution_id: str) -> str:
    """
    Emails in PBA differ from what the output uses. It unclear why. Probably out of date or a bug in the data processing by
    the PBA team.
    We need to manually fix these emails:
        carl.linnaeus@dev.eduwallet.nl to clinnaeus.uvh@dev.eduwallet.nl
        serge.delic@dev.eduwallet.nl to sdelic.uvh@dev.eduwallet.nl
        juliette.klerks@dev.eduwallet.nl to jklerks.hbot@dev.eduwallet.nl

    The .uvh or .hbot comes from the institution shortcode.
    """
    user, domain = email.split('@')

    first_name, last_name = user.split('.')
    first_letter = first_name[0]
    new_user = f'{first_letter}{last_name}'

    return f'{new_user}.{institution_id}@{domain}'


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
