from rest_framework import serializers


class IssuerSerializerV0_5(serializers.Serializer):
    """
    A representation of a badge's issuing organization is found embedded in
    0.5 badge assertions.
    """
    origin = serializers.URLField(required=True)
    name = serializers.CharField(required=True)
    org = serializers.CharField(required=False)
    contact = serializers.EmailField(required=False)


class IssuerSerializerV1_0(serializers.Serializer):
    name = serializers.CharField(required=True)
    url = serializers.URLField(required=True)
    description = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    image = serializers.URLField(required=False)
    revocationList = serializers.URLField(required=False)
