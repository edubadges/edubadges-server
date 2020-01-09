# encoding: utf-8


import openbadges.verifier
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from mainsite.utils import verify_svg
from rest_framework.exceptions import ValidationError


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


class PasswordValidator(object):
    def __call__(self, value):
        validate_password(value)
