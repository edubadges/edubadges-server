# encoding: utf-8
from __future__ import unicode_literals

from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from rest_framework.exceptions import ValidationError

from mainsite.utils import verify_svg
import openbadges.verifier


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


class ChoicesValidator(object):
    """
    Verify a value is within a set of choices
    """
    def __init__(self, choices, case_sensitive=False):
        self.case_sensitive = case_sensitive
        if self.case_sensitive:
            self.choices = choices
        else:
            self.choices = [c.lower() for c in choices]

    def __call__(self, value):
        if self.case_sensitive:
            value = value.lower()
        if value not in self.choices:
            raise ValidationError("'{}' is not supported. Only {} is available".format(value, self.choices))


class TelephoneValidator(RegexValidator):
    message = 'Telephone number does not conform to E.164'
    code = 'invalid'
    regex = r'^\+?[1-9]\d{1,14}$'

    def __init__(self, *args, **kwargs):
        super(TelephoneValidator, self).__init__(self.regex, *args, **kwargs)


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


class PasswordValidator(object):
    def __call__(self, value):
        validate_password(value)
