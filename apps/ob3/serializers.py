from typing import Any, Dict
from django.utils import timezone
from rest_framework import serializers

from apps.mainsite.settings import UI_URL

class OmitNoneFieldsMixin:
    """
    A mixin that allows serializers to automatically remove fields with None values.

    Usage:
    1. Add the mixin to your serializer class
    2. Define OMIT_IF_NONE = ['field1', 'field2'] in the serializer

    Example:
    class MySerializer(OmitNoneFieldsMixin, serializers.Serializer):
        OMIT_IF_NONE = ['description', 'optional_field']
    """
    OMIT_IF_NONE = []

    def to_representation(self, instance: Any) -> Dict[str, Any]:
        # Juggling to call the parent's to_representation method and not raise type errors
        fallback_to_representation = lambda x: dict(x.__dict__)
        representation = getattr(super(), 'to_representation', fallback_to_representation)(instance)

        for key in self.OMIT_IF_NONE:
            if representation.get(key) is None or representation.get(key) == []:
                representation.pop(key, None)

        return representation

class IssuerSerializer(serializers.Serializer):
    id = serializers.URLField()
    type = serializers.ListField(
            child=serializers.CharField(),
            read_only=True,
            default=["Profile"]
        )
    name = serializers.CharField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        """Convert the id to a URL"""
        ret['id'] = f"{UI_URL}/ob3/issuers/{ret['id']}"
        return ret

class ImageSerializer(serializers.Serializer):
    type = serializers.CharField(read_only=True, default="Image")
    id = serializers.URLField()

class AlignmentSerializer(serializers.Serializer):
    type = serializers.ListField(
            child=serializers.CharField(),
            read_only=True,
            default=["Alignment"]
    )
    targetType = serializers.CharField(
            source='target_type',
            read_only=True,
    )
    targetName = serializers.CharField(
            source='target_name',
    )
    targetDescription = serializers.CharField(
            source='target_description',
            required=False,
            allow_null=True,
    )
    targetUrl = serializers.URLField(
            source='target_url',
    )
    targetCode = serializers.CharField(
            source='target_code',
            required=False,
            allow_null=True,
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # TODO: decide on what to do if framework is missing
        # TODO: we should really make this an enum with allowed values instead
        framework = instance.get("target_framework", "")
        ret["targetType"] = f"ext:{framework}Alignment"
        return ret


class AchievementSerializer(OmitNoneFieldsMixin, serializers.Serializer):
    OMIT_IF_NONE = ['inLanguage', 'ECTS', 'educationProgramIdentifier', 'participationType', 'alignment']

    id = serializers.URLField()
    type = serializers.ListField(
            child=serializers.CharField(),
            read_only=True,
            default=["Achievement"]
    )
    criteria = serializers.DictField(child=serializers.CharField())
    description = serializers.CharField()
    name = serializers.CharField()
    image = ImageSerializer()
    inLanguage = serializers.CharField(
            source='in_language',
            required=False,
            allow_null=True,
    )
    ECTS = serializers.DecimalField(
            source='ects',
            decimal_places=1,
            max_digits=3, # Up to 99,9 ECTS (in reality, it's up to 10.0, IIRC)
            coerce_to_string=False,
    )
    educationProgramIdentifier = serializers.CharField(
            source='education_program_identifier',
            required=False,
            allow_null=True,
    )
    participationType = serializers.CharField(
            source='participation',
            required=False,
            allow_null=True,
    )
    alignment = AlignmentSerializer(many=True)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # TODO: Decide how to handle public vs private assertions: the latter won't resolve
        # TODO: DRY the id-to-url conversion
        """Convert the id to a URL"""
        ret['id'] = f"{UI_URL}/public/assertions/{ret['id']}"

        return ret

class AchievementSubjectSerializer(serializers.Serializer):
    type = serializers.ListField(
            child=serializers.CharField(),
            read_only=True,
            default=["AchievementSubject"]
    )
    achievement = AchievementSerializer()

class CredentialSerializer(OmitNoneFieldsMixin, serializers.Serializer):
    OMIT_IF_NONE = ['validFrom', 'validUntil']

    issuer = IssuerSerializer()
    validFrom = serializers.DateTimeField(
            source='valid_from',
            required=False,
            allow_null=True,
            default_timezone=timezone.utc
    )
    validUntil = serializers.DateTimeField(
            source='valid_until',
            required=False,
            allow_null=True,
            default_timezone=timezone.utc
    )
    credentialSubject = AchievementSubjectSerializer(source='credential_subject')

class OfferRequestSerializer(serializers.Serializer):
    offerId = serializers.CharField(source='offer_id')
    credentialConfigurationId = serializers.CharField(source='credential_configuration_id')
    credential = CredentialSerializer()
