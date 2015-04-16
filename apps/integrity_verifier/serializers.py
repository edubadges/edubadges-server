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
        try:
            data = data.lower()
        except AttributeError:
            raise serializers.ValidationError("Invalid data. Expected a str.")

        patterns = (
            r'^sha1\$[a-f0-9]{40}$',
            r'^sha256\$[a-f0-9]{64}$',
            r'^md5\$[a-fA-F0-9]{32}$'
        )

        if not any(re.match(pattern, data) for pattern in patterns):
            raise serializers.ValidationError(
                "Invalid data. String is not recognizably formatted.");

        return data


class AlignmentObjectSerializer(BaseFieldSerializer):
    """
    A small JSON object literal describing a BadgeClass's alignment to
    a particular standard or competency map URL.
    """
    name = serializers.CharField(required=True)
    url = serializers.URLField(required=True)
    description = serializers.CharField(required=False)


class RecipientSerializer(BaseComponentSerializer):
    """
    A representation of a 1.0 Open Badge recipient has either a hashed or
    plaintext identifier (email address).
    """
    identity = serializers.CharField(required=True)  # TODO: email | HashString
    type = serializers.CharField(required=True)
    hashed = serializers.BooleanField(required=True)


class VerificationObjectSerializer(BaseComponentSerializer):
    """
    1.0 Open Badges use a VerificationObject to indicate what authentication
    procedure a consumer should attempt and link to the relevant hosted
    verification resource, which is either a hosted copy of a badge instance
    or the issuer's public key.
    """
    type = serializers.ChoiceField(['hosted', 'signed'], required=True)
    url = serializers.URLField(required=True)


class IssuerSerializerV0_5(BaseComponentSerializer):
    """
    A representation of a badge's issuing organization is found embedded in
    0.5 badge assertions.
    """
    origin = serializers.URLField(required=True)
    name = serializers.CharField(required=True)
    org = serializers.CharField(required=False)
    contact = serializers.EmailField(required=False)


class BadgeClassSerializerV0_5(BaseComponentSerializer):
    """
    A 0.5 Open Badge assertion embedded a representation of the accomplishment
    awarded.
    """
    version = serializers.MultipleChoiceField(['0.5.0'], required=False)
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.URLField(required=True)
    criteria = serializers.URLField(required=True)
    issuer = IssuerSerializerV0_5(required=True)


class BadgeInstanceSerializerV0_5Base(BaseComponentSerializer):
    """
    Shared requirements between both 0.5 versions of the Open Badges
    specification for badge assertions.
    """
    badge = BadgeClassSerializerV0_5(required=True)
    issued_on = serializers.DateTimeField(required=False)
    expires = serializers.DateTimeField(required=False)
    evidence = serializers.URLField(required=False)


class BadgeInstanceSerializerV0_5_1(BadgeInstanceSerializerV0_5Base):
    """
    Serializer for 0.5 Open Badge assertions that have hashed recipient
    email addresses.
    """
    recipient = HashString(required=True)
    salt = serializers.CharField(required=False)


class BadgeInstanceSerializerV0_5_0(BadgeInstanceSerializerV0_5Base):
    """
    Serializer for the 0.5.0 specification version before the possibility of
    hashing a recipient identifier was introduced.
    """
    recipient = serializers.EmailField(required=True)


class IssuerSerializerV1_0(BaseComponentSerializer):
    name = serializers.CharField(required=True)
    url = serializers.URLField(required=True)
    description = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    image = serializers.URLField(required=False)
    revocationList = serializers.URLField(required=False)


class BadgeClassSerializerV1_0(BaseComponentSerializer):
    name = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    image = serializers.URLField(required=True)
    criteria = serializers.URLField(required=True)
    issuer = serializers.URLField(required=True)
    alignment = AlignmentObjectSerializer(required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class BadgeInstanceSerializerV1_0(BaseComponentSerializer):
    uid = serializers.CharField(required=True)
    recipient = RecipientSerializer(required=True)
    badge = serializers.URLField(required=True)
    issuedOn = serializers.DateTimeField(required=True)
    verify = VerificationObjectSerializer(required=True)
    image = serializers.URLField(required=False)
    expires = serializers.DateTimeField(required=False)
    evidence = serializers.URLField(required=False)
