import hashlib
import itertools
import os
import png
import re

from django.conf import settings
from django.core.files import File


CURRENT_OBI_VERSION = '1_1'
CURRENT_OBI_CONTEXT_IRI = 'https://w3id.org/openbadges/v1'


def generate_sha256_hashstring(identifier, salt):
    return 'sha256$' + hashlib.sha256(identifier+salt).hexdigest()


def generate_md5_hashstring(identifier, salt):
    return 'md5$' + hashlib.md5(identifier+salt).hexdigest()


def bake(imageFile, assertion_json_string):
    reader = png.Reader(file=imageFile)
    filepath = os.path.join(
        getattr(settings, 'MEDIA_ROOT', 'media'),
        'uploads/badges/received/%s.png' % (
            hashlib.md5(str(assertion_json_string)).hexdigest(),))
    with open(filepath, 'w') as f:
        newfile = File(f)
        chunkheader = 'openbadges\x00\x00\x00\x00\x00'
        badge_chunk = ('iTXt', bytes(chunkheader + assertion_json_string))
        png.write_chunks(newfile, baked_chunks(reader.chunks(), badge_chunk))
    newfile.close()
    return newfile


def baked_chunks(original_chunks, badge_chunk):
    def is_not_previous_assertion(chunk):
        if chunk[1].startswith('openbadges\x00'):
            return False
        return True

    first_slice = itertools.islice(original_chunks, 1)
    last_slice = itertools.ifilter(
        is_not_previous_assertion,
        itertools.islice(original_chunks, 1, None))

    return itertools.chain(first_slice, [badge_chunk], last_slice)


def is_probable_url(string):
    earl = re.compile(r'^https?')
    return earl.match(string)
