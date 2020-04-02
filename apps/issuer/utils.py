
import hashlib
import re

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
    return 'sha256$' + hashlib.sha256(key.encode('utf-8')).hexdigest()


def is_probable_url(string):
    earl = re.compile(r'^https?')
    if string is None:
        return False
    return earl.match(string)



