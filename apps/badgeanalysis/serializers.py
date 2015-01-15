# serializers.py - defines Django REST Framework serializers to be used with the API.
from rest_framework import serializers
import json
import re


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


class FullBadgeObjectFieldSerializer(WritableJSONField):
    def to_representation(self, value):
        try:
            value = super(FullBadgeObjectFieldSerializer, self).to_representation(value)
        except serializers.ValidationError as e:
            raise e
        else:
            return self.to_display_badge(value)

    def to_display_badge(self, value):
        """
        Produces a representation of a badge in JSON with each property declaring its type.
        Current type options are "text", "link", and "image"
        Each property looks like: {
            "type": "image",
            "text": "alt text",
            "href": "/media/images/heeeeeyyy.png"
        }
        Required fields:
        assertion: { issuedOn, evidence },
        badgeclass: { image, name, description, criteria },
        issuerorg (as a link property)
        """
        def type_for_prop(badge_object, prop):
            types = {
                "assertion": {
                    "issuedOn": "text",
                    "evidence": "link"
                },
                "badgeclass": {
                    "name": "text",
                    "description": "text",
                    "criteria": "link"
                },
                "issuerorg": "link"
            }
            result = types.get(badge_object)
            if isinstance(result, dict):
                return result.get(prop)
            else:
                return result

        def fetch_from_value(badge_object, prop, label=None):
            native_prop = value.get(badge_object, {}).get(prop, "")
            prop_type = type_for_prop(badge_object, prop)
            result = {
                "type": prop_type
            }

            if prop_type == "text":
                result['text'] = str(native_prop)
            elif prop_type == "link":
                result['href'] = str(native_prop)
                if label:
                    result['text'] = label
            return result

        serialization = {
            "assertion": {
                "issuedOn": fetch_from_value("assertion", "issuedOn"),
                "evidence": fetch_from_value("assertion", "evidence")
            },
            "badgeclass": {
                "name": fetch_from_value("badgeclass", "name"),
                "description": fetch_from_value("badgeclass", "description"),
                "criteria": fetch_from_value("badgeclass", "criteria")
            },
            # Use the issuerorg name as the label of a link.
            "issuerorg": fetch_from_value("issuerorg", "url", value.get('issuerorg', {}).get("name", None))
        }
        return serialization


class BadgeImagePropertySerializer(serializers.CharField):
    def to_representation(self, value):
        def get_href(value):
            uploads = re.compile(r'^uploads/')
            method_prefix = re.compile(r'^[http://|https://|/]')
            if uploads.match(value):
                return '/media/' + value
            elif method_prefix.match(value):
                return value
            else:
                return '/' + value

        serialization = {
            "type": "image",
            "text": "Badge Image",
            "href": get_href(str(value))
        }
        return serialization


class BadgeSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    recipient_input = serializers.CharField(max_length=2048)
    image = BadgeImagePropertySerializer(max_length=2048)
    full_badge_object = FullBadgeObjectFieldSerializer(max_length=16384, read_only=True, required=False)
