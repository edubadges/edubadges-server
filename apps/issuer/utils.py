from __future__ import unicode_literals
import hashlib
import re

from django.apps import apps
from django.conf import settings
from django.core.urlresolvers import resolve, Resolver404

from mainsite.utils import OriginSetting

CURRENT_OBI_VERSION = '1_1'
CURRENT_OBI_CONTEXT_IRI = 'https://w3id.org/openbadges/v1'


def generate_sha256_hashstring(identifier, salt):
    return 'sha256$' + hashlib.sha256(identifier+salt).hexdigest()


def generate_md5_hashstring(identifier, salt):
    return 'md5$' + hashlib.md5(identifier+salt).hexdigest()


def is_probable_url(string):
    earl = re.compile(r'^https?')
    if string is None:
        return False
    return earl.match(string)


def obscure_email_address(email):
    charlist = list(email)

    return ''.join(letter if letter in ('@', '.',) else '*' for letter in charlist)


def get_badgeclass_by_identifier(identifier):
    """
    Finds a Issuer.BadgeClass by an identifier that can be either:
        - JSON-ld id
        - BadgeClass.id
        - BadgeClass.slug
    """

    from issuer.models import BadgeClass

    # attempt to resolve identifier as JSON-ld id
    if identifier.startswith(OriginSetting.JSON):
        try:
            resolver_match = resolve(identifier.replace(OriginSetting.JSON, ''))
            if resolver_match:
                badgeclass_slug = resolver_match.kwargs.get('slug', None)
                if badgeclass_slug:
                    try:
                        return BadgeClass.cached.get(slug=badgeclass_slug)
                    except BadgeClass.DoesNotExist:
                        pass
        except Resolver404:
            pass

    # attempt to resolve as BadgeClass.slug
    try:
        return BadgeClass.cached.get(slug=identifier)
    except BadgeClass.DoesNotExist:
        pass

    # attempt to resolve as BadgeClass.id
    try:
        return BadgeClass.cached.get(pk=identifier)
    except (BadgeClass.DoesNotExist, ValueError):
        pass

    # attempt to resolve as JSON-ld of external badge
    try:
        return BadgeClass.cached.get(source_url=identifier)
    except BadgeClass.DoesNotExist:
        pass

    # nothing found
    return None
