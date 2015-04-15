import re

from rest_framework import serializers


class BaseComponentSerializer(serializers.Serializer):
    pass


class BaseFieldSerializer(serializers.Field):
    pass


class HashString(BaseFieldSerializer):
    """
    A representation of a badge recipient identifier that indicates a hashing
    algorithm and hashed value.
    """
    def to_internal_value(self, data):
        data = data.lower()
        patterns = (
            r'^sha1\$[a-f0-9]{40}$',
            r'^sha256\$[a-f0-9]{64}$',
            r'^md5\$[a-fA-F0-9]{32}$'
        )

        if not any(re.match(pattern, data) for pattern in patterns):
            raise serializers.ValidationError

        return data


class IssuerSerializerV0_5(BaseComponentSerializer):
    """
    A representation of a badge's issuing organization is found embedded in
    0.5 badge assertions.
    """
    origin = serializers.URLField(required=True)
    name = serializers.CharField(required=True)
    org = serializers.CharField()
    contact = serializers.EmailField()


class BadgeClassSerializerV0_5(BaseComponentSerializer):
    """
    A 0.5 Open Badge assertion embedded a representation of the accomplishment
    awarded.
    """
    version = serializers.RegexField(r'^0\.5\.0$', allow_blank=False, required=False)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.URLField(required=True)
    criteria = serializers.URLField(required=True)
    issuer = IssuerSerializerV0_5(required=True)


class BadgeInstanceSerializerV0_5Base(BaseComponentSerializer):
    """
    Shared requirements between both 0.5 versions of the Open Badges
    specification for badge assertions
    """
    badge = BadgeClassSerializerV0_5(required=True)
    issued_on = serializers.DateTimeField()
    expires = serializers.DateTimeField()
    evidence = serializers.URLField()


class BadgeInstanceSerializerV0_5_1(BadgeInstanceSerializerV0_5Base):
    """
    Serializer for 0.5 Open Badge assertions that have hashed recipient
    email addresses.
    """
    recipient = HashString(required=True)
    salt = serializers.CharField()


class BadgeInstanceSerializerV0_5_0(BadgeInstanceSerializerV0_5Base):
    """
    Serializer for the 0.5.0 specification version before the possibility of
    hashing a recipient identifier was introduced.
    """
    recipient = serializers.EmailField(required=True)
