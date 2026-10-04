import base64
import binascii
import mimetypes
import sys
import urllib.parse
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile
from django.utils.translation import gettext as _
from mainsite.validators import ValidImageValidator
from rest_framework.exceptions import ValidationError
from rest_framework.fields import FileField, SkipField


class Base64FileField(FileField):
    # mimetypes.guess_extension() may return different values for same mimetype, but we need one extension for one mime
    _MIME_MAPPING = {"image/jpeg": ".jpg", "audio/wav": ".wav"}
    _ERROR_MESSAGE = _("Base64 string is incorrect")

    def to_internal_value(self, data):
        if isinstance(data, UploadedFile):
            return super().to_internal_value(data)

        try:
            mime, encoded_data = data.replace("data:", "", 1).split(";base64,")
            extension = (
                self._MIME_MAPPING[mime] if mime in list(self._MIME_MAPPING.keys()) else mimetypes.guess_extension(mime)
            )
            ret = ContentFile(
                base64.b64decode(encoded_data),
                name=f"{uuid.uuid4()!s}{extension}",
            )
            filesize = sys.getsizeof(ret.file)
            if filesize > settings.MAX_IMAGE_UPLOAD_SIZE:
                raise ValidationError(f"Image too large, max file size is {settings.MAX_IMAGE_UPLOAD_SIZE_LABEL}", 999)
            return ret
        except (ValueError, binascii.Error):
            return super().to_internal_value(data)


class ValidImageField(Base64FileField):
    default_validators = [ValidImageValidator()]

    def __init__(self, skip_http=True, allow_empty_file=False, use_url=True, allow_null=True, **kwargs):
        self.skip_http = skip_http
        super().__init__(allow_empty_file=allow_empty_file, use_url=use_url, allow_null=allow_null, **kwargs)

    def to_internal_value(self, data):
        # Skip http/https urls to avoid overwriting valid data when, for example, a client GETs and subsequently PUTs an
        # entity containing an image URL.
        if (
            self.skip_http
            and not isinstance(data, UploadedFile)
            and urllib.parse.urlparse(data).scheme in ("http", "https")
        ):
            raise SkipField()

        return super().to_internal_value(data)
