# serializers.py - defines Django REST Framework serializers to be used with the API.
from rest_framework import serializers
from badgeanalysis.models import OpenBadge
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
                    "image": "image",
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
            native_prop = value.get(badge_object, {}).get(prop, "");
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
            elif prop_type == "image":
                non_rel = re.compile(r'^[http://|https://|/]')
                result['text'] = "Badge Image"
                if non_rel.match(str(native_prop)):
                    result['href'] = str(native_prop)
                else:
                    result['href'] = '/' + str(native_prop)
            return result

        serialization = {
            "assertion": {
                "issuedOn": fetch_from_value("assertion", "issuedOn"),
                "evidence": fetch_from_value("assertion", "evidence")
            },
            "badgeclass": {
                "image": fetch_from_value("badgeclass", "image"),
                "name": fetch_from_value("badgeclass", "name"),
                "description": fetch_from_value("badgeclass", "description"),
                "criteria": fetch_from_value("badgeclass", "criteria")
            },
            "issuerorg": fetch_from_value("issuerorg", "url", fetch_from_value("issuerorg", "name"))
        }
        return serialization

class BadgeSerializer(serializers.Serializer):
    pk = serializers.IntegerField()
    recipient_input = serializers.CharField(max_length=2048)
    image = serializers.CharField(max_length=512)
    full_badge_object = FullBadgeObjectFieldSerializer(max_length=16384, read_only=True, required=False)
