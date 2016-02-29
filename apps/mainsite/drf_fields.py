import base64
import mimetypes
import binascii
import uuid

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import ugettext as _

from rest_framework import serializers
from rest_framework.fields import FileField


class Base64FileField(FileField):

    # mimetypes.guess_extension() may return different values for same mimetype, but we need one extension for one mime
    _MIME_MAPPING = {
        'image/jpeg': '.jpg',
        'audio/wav': '.wav'
    }
    _ERROR_MESSAGE = _('Base64 string is incorrect')

    def to_internal_value(self, data):
        if isinstance(data, InMemoryUploadedFile):
            return super(Base64FileField, self).to_internal_value(data)

        try:
            mime, encoded_data = data.replace('data:', '', 1).split(';base64,')
            extension = self._MIME_MAPPING[mime] if mime in self._MIME_MAPPING.keys() else mimetypes.guess_extension(mime)
            ret = ContentFile(base64.b64decode(encoded_data), name='{name}{extension}'.format(name=str(uuid.uuid4()),
                                                                                              extension=extension))
            return ret
        except (ValueError, binascii.Error):
            return super(Base64FileField, self).to_internal_value(data)

