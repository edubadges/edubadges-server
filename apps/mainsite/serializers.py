import json
from collections import OrderedDict
import collections

import rest_framework
from django.conf import settings
from django.http import Http404
from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework import status, exceptions
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.serializers import ListSerializer
from six import string_types

from entity.serializers import BaseSerializerV2
from mainsite.pagination import EncryptedCursorPagination


class HumanReadableBooleanField(serializers.BooleanField):
    TRUE_VALUES = serializers.BooleanField.TRUE_VALUES | set(('on', 'On', 'ON'))
    FALSE_VALUES = serializers.BooleanField.FALSE_VALUES | set(('off', 'Off', 'OFF'))


class ReadOnlyJSONField(serializers.CharField):

    def to_representation(self, value):
        if isinstance(value, (dict, list)):
            return value
        else:
            raise serializers.ValidationError("WriteableJsonField: Did not get a JSON-serializable datatype from storage for this item: " + str(value))


class WritableJSONField(ReadOnlyJSONField):
    def to_internal_value(self, data):
        try:
            internal_value = json.loads(data)
        except Exception:
            # TODO: this is going to choke on dict input, when it should be allowed in addition to JSON.
            raise serializers.ValidationError("WriteableJsonField: Could not process input into a python dict for storage " + str(data))

        return internal_value


class LinkedDataEntitySerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(LinkedDataEntitySerializer, self).to_representation(instance)
        representation['@id'] = instance.jsonld_id

        try:
            representation['@type'] = self.jsonld_type
        except AttributeError:
            pass

        return representation


class LinkedDataReferenceField(serializers.Serializer):
    """
    A read-only field for embedding representations of entities that have Linked Data identifiers.
    Includes their @id by default and any additional identifier keys that are the named
    properties on the instance.
    """
    def __init__(self, keys=[], model=None, read_only=True, field_names=None, **kwargs):
        kwargs.pop('many', None)
        super(LinkedDataReferenceField, self).__init__(read_only=read_only, **kwargs)
        self.included_keys = keys
        self.model = model
        self.field_names = field_names

    def to_representation(self, obj):
        output = OrderedDict()
        output['@id'] = obj.jsonld_id

        for key in self.included_keys:
            field_name = key
            if self.field_names is not None and key in self.field_names:
                field_name = self.field_names.get(key)
            output[key] = getattr(obj, field_name, None)

        return output

    def to_internal_value(self, data):
        if not isinstance(data, basestring):
            idstring = data.get('@id')
        else:
            idstring = data

        try:
            return self.model.cached.get_by_id(idstring)
        except AttributeError:
            raise TypeError(
                "LinkedDataReferenceField model must be declared and use cache " +
                "manager that implements get_by_id method."
            )

class LinkedDataReferenceList(serializers.ListField):
    # child must be declared in implementation.
    def get_value(self, dictionary):
        try:
            return dictionary.getlist(self.field_name, serializers.empty)
        except AttributeError:
            return dictionary.get(self.field_name, serializers.empty)


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
        super(StripTagsCharField, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        value = super(StripTagsCharField, self).to_internal_value(data)
        if self.strip_tags:
            return strip_tags(value)
        return value


class MarkdownCharFieldValidator(object):
    def __call__(self, value):
        if '![' in value:
            raise ValidationError('Images not supported in markdown')


class MarkdownCharField(StripTagsCharField):
    default_validators = [MarkdownCharFieldValidator()]


class VerifiedAuthTokenSerializer(AuthTokenSerializer):
    def validate(self, attrs):
        attrs = super(VerifiedAuthTokenSerializer, self).validate(attrs)
        user = attrs.get('user')
        if not user.verified:
            try:
                email = user.cached_emails()[0]
                email.send_confirmation()
            except IndexError as e:
                pass
            raise ValidationError('You must verify your primary email address before you can sign in.')
        return attrs


class OriginalJsonSerializerMixin(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(OriginalJsonSerializerMixin, self).to_representation(instance)

        if hasattr(instance, 'get_filtered_json'):
            # properties in original_json not natively supported
            extra_properties = instance.get_filtered_json()
            if extra_properties and len(extra_properties) > 0:
                representation.update(extra_properties)

        return representation


class CursorPaginatedListSerializer(serializers.ListSerializer):

    def __init__(self, queryset, request, *args, **kwargs):
        self.paginator = EncryptedCursorPagination()
        self.page = self.paginator.paginate_queryset(queryset, request)
        super(CursorPaginatedListSerializer, self).__init__(data=self.page, *args, **kwargs)

    def to_representation(self, data):
        representation = super(CursorPaginatedListSerializer, self).to_representation(data)
        envelope = BaseSerializerV2.response_envelope(result=representation,
                                                      success=True,
                                                      description='ok')
        envelope['pagination'] = self.paginator.get_page_info()
        return envelope

    @property
    def data(self):
        return super(serializers.ListSerializer, self).data
