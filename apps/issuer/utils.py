
import hashlib
import re

from django.apps import apps
from django.conf import settings
from django.urls import resolve, Resolver404

from mainsite.utils import OriginSetting


OBI_VERSION_CONTEXT_IRIS = {
    '1_1': 'https://w3id.org/openbadges/v1',
    '2_0': 'https://w3id.org/openbadges/v2',
}

CURRENT_OBI_VERSION = '2_0'
CURRENT_OBI_CONTEXT_IRI = OBI_VERSION_CONTEXT_IRIS.get(CURRENT_OBI_VERSION)

# assertions that were baked and saved to BadgeInstance.image used this version
UNVERSIONED_BAKED_VERSION = '2_0'


def get_obi_context(obi_version):
    context_iri = OBI_VERSION_CONTEXT_IRIS.get(obi_version, None)
    if context_iri is None:
        obi_version = CURRENT_OBI_VERSION
        context_iri = CURRENT_OBI_CONTEXT_IRI
    return (obi_version, context_iri)


def add_obi_version_ifneeded(url, obi_version):
    if obi_version == CURRENT_OBI_VERSION:
        return url
    if not url.startswith(OriginSetting.HTTP):
        return url
    return "{url}{sep}v={obi_version}".format(
        url=url,
        sep='&' if '?' in url else '?',
        obi_version=obi_version)


def generate_sha256_hashstring(identifier, salt=None):
    key = '{}{}'.format(identifier, salt if salt is not None else "")
    return 'sha256$' + hashlib.sha256(key).hexdigest()


def generate_md5_hashstring(identifier, salt=None):
    key = '{}{}'.format(identifier, salt if salt is not None else "")
    return 'md5$' + hashlib.md5(key).hexdigest()


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
    if identifier.startswith(OriginSetting.HTTP):
        try:
            resolver_match = resolve(identifier.replace(OriginSetting.HTTP, ''))
            if resolver_match:
                entity_id = resolver_match.kwargs.get('entity_id', None)
                if entity_id:
                    try:
                        return BadgeClass.cached.get(entity_id=entity_id)
                    except BadgeClass.DoesNotExist:
                        pass
        except Resolver404:
            pass

    # attempt to resolve as BadgeClass.slug
    try:
        return BadgeClass.cached.get(slug=identifier)
    except BadgeClass.DoesNotExist:
        pass

    # attempt to resolve as BadgeClass.entity_id
    try:
        return BadgeClass.cached.get(entity_id=identifier)
    except (BadgeClass.DoesNotExist, ValueError):
        pass

    # attempt to resolve as JSON-ld of external badge
    try:
        return BadgeClass.cached.get(source_url=identifier)
    except BadgeClass.DoesNotExist:
        pass

    # nothing found
    return None


def mapExtensionsToDict(request):
    if request.data.get('extensions', None):
        d = {}
        for ext in request.data['extensions']:
            key = list(ext.keys())[0]
            d[key] = ext[key]
        request.data['extensions'] = d
    else:
        request.data['extensions'] = {}
            
