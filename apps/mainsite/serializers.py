import json
from collections import OrderedDict

from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import SlugRelatedField

from mainsite.exceptions import BadgrValidationError


class BaseSlugRelatedField(SlugRelatedField):
    def get_queryset(self):
        return self.model.objects.all()


class HumanReadableBooleanField(serializers.BooleanField):
    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | set(('on', 'On', 'ON'))
    FALSE_VALUES = serializers.BooleanField.FALSE_VALUES | set(('off', 'Off', 'OFF'))


class BadgrBaseModelSerializer(serializers.ModelSerializer):

    def is_valid(self, raise_exception=False):
        try:
            return super(BadgrBaseModelSerializer, self).is_valid(raise_exception)
        except ValidationError as e:
            raise BadgrValidationError(error_message=e.detail, error_code=999)


class LinkedDataEntitySerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(LinkedDataEntitySerializer, self).to_representation(instance)
        representation['@id'] = instance.jsonld_id

        try:
            representation['@type'] = self.jsonld_type
        except AttributeError:
            pass

        return representation


class JSONDictField(serializers.DictField):
    """
    A DictField that also accepts JSON strings as input
    """

    def to_internal_value(self, data):
        try:
            data = json.loads(data)
        except TypeError:
            pass

        return super(JSONDictField, self).to_internal_value(data)


class StripTagsCharField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        self.strip_tags = kwargs.pop('strip_tags', True)
        self.convert_null = kwargs.pop('convert_null', False)  # Converts db nullable fields to empty strings
        super(StripTagsCharField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        value = super(StripTagsCharField, self).to_internal_value(data)
        if self.strip_tags:
            return strip_tags(value)
        return value

    def get_attribute(self, instance):
        value = super(StripTagsCharField, self).get_attribute(instance)
        if self.convert_null:
            return value if value is not None else ""
        return value


class MarkdownCharFieldValidator(object):
    def __call__(self, value):
        if '![' in value:
            raise ValidationError('Images not supported in markdown')


class MarkdownCharField(StripTagsCharField):
    default_validators = [MarkdownCharFieldValidator()]


class OriginalJsonSerializerMixin(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(OriginalJsonSerializerMixin, self).to_representation(instance)

        if hasattr(instance, 'get_filtered_json'):
            # properties in original_json not natively supported
            extra_properties = instance.get_filtered_json()
            if extra_properties and len(extra_properties) > 0:
                representation.update(extra_properties)

        return representation
