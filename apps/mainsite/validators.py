# encoding: utf-8
from __future__ import unicode_literals

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



