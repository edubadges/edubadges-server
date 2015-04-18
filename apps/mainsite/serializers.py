import json

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
