import json
from collections import OrderedDict

from django.conf import settings

from rest_framework import serializers


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


class LinkedDataReferenceField(serializers.RelatedField):
    """
    A read-only field for embedding representations of entities that have Linked Data identifiers.
    Includes their @id by default and any additional identifier keys that are the named
    properties on the instance.
    """
    def __init__(self, included_keys=[], model=None, read_only=True, **kwargs):
        if kwargs.get('many') is not None:
            kwargs.pop('many')
        super(LinkedDataReferenceField, self).__init__(read_only=read_only, **kwargs)
        self.included_keys = included_keys
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
