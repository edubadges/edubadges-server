import hashlib
import itertools
import os.path
import png
import re

from django.core.files.base import ContentFile


def unbake(imageFile):
    """
    Return the openbadges content contained in a baked PNG file.
    If this doesn't work, return None.

    If there is both an iTXt and tEXt chunk with keyword openbadges,
    the iTXt chunk content will be returned.
    """

    reader = png.Reader(file=imageFile)
    for chunktype, content in reader.chunks():
        if chunktype == 'iTXt' and content.startswith('openbadges\x00'):
            return re.sub('openbadges[\x00]+', '', content)
        elif chunktype == 'tEXt' and content.startswith('openbadges\x00'):
            return content.split('\x00')[1]


def bake(imageFile, assertion_json_string):
    """
    Embeds a serialized representation of a badge instance in a PNG image file.
    """
    reader = png.Reader(file=imageFile)

    output_filename = '%s.png' % hashlib.md5(str(assertion_json_string)).hexdigest()

    newfile = ContentFile("", name=output_filename)
    newfile.open()
    chunkheader = 'openbadges\x00\x00\x00\x00\x00'
    badge_chunk = ('iTXt', bytes(chunkheader + assertion_json_string))
    png.write_chunks(newfile, baked_chunks(reader.chunks(), badge_chunk))

    newfile.close()
    return newfile


def baked_chunks(original_chunks, badge_chunk):
    """
    Returns an iterable of chunks that places the Open Badges baked chunk
    and filters out any previous Open Badges chunk that may have existed.
    """
    def is_not_previous_assertion(chunk):
        if chunk[1].startswith('openbadges\x00'):
            return False
        return True

    first_slice = itertools.islice(original_chunks, 1)
    last_slice = itertools.ifilter(
        is_not_previous_assertion,
        itertools.islice(original_chunks, 1, None)
    )

    return itertools.chain(first_slice, [badge_chunk], last_slice)
