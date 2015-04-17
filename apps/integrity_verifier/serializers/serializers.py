from rest_framework import serializers


class AlignmentObjectSerializer(serializers.Serializer):
    """
    A small JSON object literal describing a BadgeClass's alignment to
    a particular standard or competency map URL.
    """
    name = serializers.CharField(required=True)
    url = serializers.URLField(required=True)
    description = serializers.CharField(required=False)


class RecipientSerializer(serializers.Serializer):
    """
    A representation of a 1.0 Open Badge recipient has either a hashed or
    plaintext identifier (email address).
    """
    identity = serializers.CharField(required=True)  # TODO: email | HashString
    type = serializers.CharField(required=True)
    hashed = serializers.BooleanField(required=True)


class VerificationObjectSerializer(serializers.Serializer):
    """
    1.0 Open Badges use a VerificationObject to indicate what authentication
    procedure a consumer should attempt and link to the relevant hosted
    verification resource, which is either a hosted copy of a badge instance
    or the issuer's public key.
    """
    type = serializers.ChoiceField(['hosted', 'signed'], required=True)
    url = serializers.URLField(required=True)
