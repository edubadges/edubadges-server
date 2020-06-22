# encoding: utf-8

import openbadges.verifier

from django.contrib.auth.password_validation import validate_password
from rest_framework.exceptions import ValidationError

from mainsite.utils import verify_svg
from issuer.helpers import DjangoCacheRequestsCacheBackend

class ValidImageValidator(object):
    """
    Verify a value is file-like and is either a PNG or a SVG
    """
    def __call__(self, image):
        if image:
            try:
                from PIL import Image
                img = Image.open(image)
                img.verify()
            except Exception as e:
                if not verify_svg(image):
                    raise ValidationError('Invalid image.')
            else:
                if img.format != "PNG":
                    raise ValidationError('Invalid PNG')


class PasswordValidator(object):
    def __call__(self, value):
        validate_password(value)


class BadgeExtensionValidator(object):
    message = "Invalid OpenBadges Extension"

    def __call__(self, value):
        if len(value) > 0:
            result = openbadges.verifier.validate_extensions(value.copy())
            report = result.get('report', {})
            if not report.get('valid', False):
                messages = report.get('messages', [])
                if len(messages) > 0:
                    msg = messages[0].get('result', self.message)
                else:
                    msg = self.message
                raise ValidationError(msg)
