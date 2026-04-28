# encoding: utf-8

from rest_framework.exceptions import ValidationError
from mainsite.utils import verify_svg
import requests
from jsonschema import validate, ValidationError as JsonSchemaValidationError


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



class SimpleExtensionValidator:
    def __init__(self, cache=None):
        self.cache = cache or {}

    def fetch_schema(self, url):
        if url in self.cache:
            return self.cache[url]

        response = requests.get(url, timeout=5)
        response.raise_for_status()
        schema = response.json()
        self.cache[url] = schema
        return schema

    def validate(self, extension_input):
        errors = []

        context = extension_input.get("@context", {})
        validations = context.get("obi:validation", [])

        if not validations:
            return {
                "valid": False,
                "messages": ["No validation rules found in context"]
            }

        for rule in validations:
            ext_type = rule.get("obi:validatesType")
            schema_url = rule.get("obi:validationSchema")

            if not ext_type or not schema_url:
                errors.append("Invalid validation rule in context")
                continue

            # Extract extension key (e.g. "ECTS")
            short_name = ext_type.split(":")[-1].replace("Extension", "")

            if short_name not in extension_input:
                errors.append(f"Missing extension field: {short_name}")
                continue

            try:
                schema = self.fetch_schema(schema_url)

                validate(
                    instance={short_name: extension_input[short_name]},
                    schema=schema
                )

            except JsonSchemaValidationError as e:
                errors.append(f"{short_name}: {e.message}")

            except Exception as e:
                errors.append(f"Schema fetch/validation failed: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "messages": errors
        }


class BadgeExtensionValidator:
    message = "Invalid OpenBadges Extension"

    def __init__(self):
        self.validator = SimpleExtensionValidator()

    def __call__(self, value):
        if len(value) > 0:
            result = self.validator.validate(value.copy())

            if not result["valid"]:
                raise ValidationError(
                    result["messages"] or self.message
                )
