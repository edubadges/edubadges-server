import os
import csv
from typing_extensions import Optional

from django.core.files import File

from badgeuser.models import Terms, TermsUrl
from institution.models import Institution


def seed_image_for(type: str, name: str) -> File:
    base_path = 'apps/mainsite/seeds/images/'
    if type == 'institutions':
        raise ValueError('NOTE: path for institutions is inconsistent and must be singular: institution')

    path = os.path.join(base_path, type, name)
    return File(open(path, 'rb'), name)


def add_terms_institution(institution: Institution) -> None:
    formal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_FORMAL_BADGE)
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-agreement-nl.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=formal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/formal-edubadges-excerpt-nl.md',
    )
    informal_badge_terms, _ = Terms.objects.get_or_create(institution=institution, terms_type=Terms.TYPE_INFORMAL_BADGE)
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=False,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-agreement-nl.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_ENGLISH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-en.md',
    )
    TermsUrl.objects.get_or_create(
        terms=informal_badge_terms,
        language=TermsUrl.LANGUAGE_DUTCH,
        excerpt=True,
        url='https://raw.githubusercontent.com/edubadges/privacy/master/university-example.org/informal-edubadges-excerpt-nl.md',
    )


def read_seed_csv(csv_name: str) -> list[dict[str, str]]:
    file_path = os.path.join('apps/mainsite/seeds/data', f'{csv_name}.csv')
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file, delimiter=';', strict=True)
        return list(reader)


def institution_by_shortcode(shortcode: str) -> Institution:
    return Institution.objects.get(identifier=institution_id_by_shortcode(shortcode))


def institution_id_by_shortcode(shortcode: str) -> Optional[str]:
    map = {
        'mbob': 'mbob.nl',
        'uvh': 'uvh.nl',
        'tun': 'tun.nb',
        'hbot': 'hbot.nl',
    }
    # NOTE: following don't have an url identifier defined in the PBA yet
    # 'eur': '61PL',
    # 'ah': '57GL',
    # 'nhls': '21FD',
    return map.get(shortcode)


def institution_id_by_pba_id(identifier: str) -> Optional[str]:
    map = {
        '11BR': 'mbob.nl',
        '41GM': 'uvh.nl',
        'XXID': 'tun.nb',
        '87TS': 'hbot.nl',
    }
    # NOTE:  Following ids don't have a shortcode in the form of an URL yet in the PBA
    #     '61PL': 'eur.nl',
    #     '57GL': 'ahb.nl',
    #     '21FD': 'nhls.nl',
    return map.get(identifier)


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
