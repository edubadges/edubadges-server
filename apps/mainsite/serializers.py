import json
from collections import OrderedDict

from django.conf import settings
from rest_framework import serializers


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
    def __init__(self, keys=[], model=None, read_only=True, **kwargs):
        kwargs.pop('many', None)
        super(LinkedDataReferenceField, self).__init__(read_only=read_only, **kwargs)
        self.included_keys = keys
        self.model = model

    def to_representation(self, obj):
        output = OrderedDict()
        output['@id'] = obj.jsonld_id

        for key in self.included_keys:
            try:
                output[key] = getattr(obj, key)
            except AttributeError:
                try:
                    output[key] = obj[key]
                except KeyError:
                    output[key] = None

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
