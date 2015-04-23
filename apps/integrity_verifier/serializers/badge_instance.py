from rest_framework import serializers

import badge_class
from .fields import BadgeDateTimeField, HashString
from .serializers import RecipientSerializer, VerificationObjectSerializer


class V0_5Base(serializers.Serializer):
    """
    Shared requirements between both 0.5 versions of the Open Badges
    specification for badge assertions.
    """
    badge = badge_class.BadgeClassSerializerV0_5(required=True)
    issued_on = BadgeDateTimeField(required=False)
    expires = BadgeDateTimeField(required=False)
    evidence = serializers.URLField(required=False)


class BadgeInstanceSerializerV0_5_1(V0_5Base):
    """
    Serializer for 0.5 Open Badge assertions that have hashed recipient
    email addresses.
    """
    recipient = HashString(required=True)
    salt = serializers.CharField(required=False)


class BadgeInstanceSerializerV0_5_0(V0_5Base):
    """
    Serializer for the 0.5.0 specification version before the possibility of
    hashing a recipient identifier was introduced.
    """
    recipient = serializers.EmailField(required=True)


class BadgeInstanceSerializerV1_0(serializers.Serializer):
    uid = serializers.CharField(required=True)
    recipient = RecipientSerializer(required=True)
    badge = serializers.URLField(required=True)
    issuedOn = BadgeDateTimeField(required=True)
    verify = VerificationObjectSerializer(required=True)
    image = serializers.URLField(required=False)
    expires = BadgeDateTimeField(required=False)
    evidence = serializers.URLField(required=False)
