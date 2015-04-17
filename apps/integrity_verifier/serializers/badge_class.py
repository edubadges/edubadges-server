from rest_framework import serializers

import issuer
from .serializers import AlignmentObjectSerializer


class BadgeClassSerializerV0_5(serializers.Serializer):
    """
    A 0.5 Open Badge assertion embedded a representation of the accomplishment
    awarded.
    """
    version = serializers.ChoiceField(['0.5.0'], required=False)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.URLField(required=True)
    criteria = serializers.URLField(required=True)
    issuer = issuer.IssuerSerializerV0_5(required=True)


class BadgeClassSerializerV1_0(serializers.Serializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.URLField(required=True)
    criteria = serializers.URLField(required=True)
    issuer = serializers.URLField(required=True)
    alignment = AlignmentObjectSerializer(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
