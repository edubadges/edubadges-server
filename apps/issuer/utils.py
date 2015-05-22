import hashlib
import re


CURRENT_OBI_VERSION = '1_1'
CURRENT_OBI_CONTEXT_IRI = 'https://w3id.org/openbadges/v1'


def generate_sha256_hashstring(identifier, salt):
    return 'sha256$' + hashlib.sha256(identifier+salt).hexdigest()


def generate_md5_hashstring(identifier, salt):
    return 'md5$' + hashlib.md5(identifier+salt).hexdigest()


def is_probable_url(string):
    earl = re.compile(r'^https?')
    return earl.match(string)
