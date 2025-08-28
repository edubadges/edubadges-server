# encoding: utf-8

import openbadges.verifier
from rest_framework.exceptions import ValidationError

from mainsite.utils import verify_svg


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


class BadgeExtensionValidator(object):
    message = "Invalid OpenBadges Extension"

    def __call__(self, value):
        if len(value) > 0:
            options = {"use_cache": True, "cache_expire_after": 60 * 60 * 24,
                       "jsonld_options": {"compactArrays": False}}
            try:
                result = openbadges.verifier.validate_extensions(value.copy(), **options)
                report = result.get('report', {})
            except Exception as e:
                raise ValidationError(f"Unable to verify badge extensions: {str(e)}")
            if not report.get('valid', False):
                messages = report.get('messages', [])
                if len(messages) > 0:
                    msg = [message.get('result', self.message) for message in messages]
                else:
                    msg = self.message
                raise ValidationError(msg)
