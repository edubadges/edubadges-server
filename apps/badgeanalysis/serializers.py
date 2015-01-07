# serializers.py - defines Django REST Framework serializers to be used with the API.
from rest_framework import serializers
from badgeanalysis.models import OpenBadge
import json


class WritableJSONField(serializers.CharField):
    def to_internal_value(self, data):
        try: 
            internal_value = json.loads(data)
        except Exception:
            raise serializers.ValidationError("Could not process input into a python dict for storage " + str(data))

        return internal_value

    def to_representation(self, value):
        if isinstance(value, dict):
            return value
        else:
            raise serializers.ValidationError("Did not get a dict from the JSON stored for this item: " + str(value))


class BadgeSerializer(serializers.Serializer):
    recipient_input = serializers.CharField(max_length=2048)
    image = serializers.CharField(max_length=512)
    full_badge_object = WritableJSONField(max_length=16384)
