# encoding: utf-8


from django.contrib.auth.password_validation import validate_password
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


class PasswordValidator(object):
    def __call__(self, value):
        validate_password(value)
