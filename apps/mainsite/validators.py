# encoding: utf-8
from rest_framework.exceptions import ValidationError

from mainsite.extensions_validators import BaseExtensionValidator
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


class ExtensionValidator:
    """
    Core validator that loops over extensions and delegates
    to the registered validators.
    """

    @staticmethod
    def validate(extension_input: dict):
        errors = []

        for ext_key, ext_value in extension_input.items():
            validator = BaseExtensionValidator.REGISTRY.get(ext_key)

            if not validator:
                errors.append(f"Unknown extension: {ext_key}")
                continue

            ext_errors = validator.validate(ext_value)
            errors.extend(f"{ext_key}: {err}" for err in ext_errors)

        return {
            "valid": len(errors) == 0,
            "messages": errors,
        }


class BadgeExtensionValidator:
    message = "Invalid OpenBadges Extension"

    def __init__(self):
        self.validator = ExtensionValidator()

    def __call__(self, value):
        if not value:
            return

        result = self.validator.validate(value.copy())

        if not result["valid"]:
            raise ValidationError(result["messages"] or self.message)
