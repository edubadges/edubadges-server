import hashlib
import re

from django.apps import apps
from django.conf import settings


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


def badgr_import_url(instance):
    if apps.is_installed('composition'):
        return getattr(settings, 'HTTP_ORIGIN') \
            + '/earner/badges/new?url=' + instance.get_full_url()


def obscure_email_address(email):
    charlist = list(email)

    return ''.join(letter if letter in ('@', '.',) else '*' for letter in charlist)
