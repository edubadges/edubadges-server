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
            representation.pop(key, None) if representation.get(key) is None else None

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

class AchievementSerializer(OmitNoneFieldsMixin, serializers.Serializer):
    OMIT_IF_NONE = ['inLanguage', 'ECTS']

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

class EduCredentialSerializer(serializers.Serializer):
    offerId = serializers.CharField(source='offer_id')
    credentialConfigurationId = serializers.CharField(source='credential_configuration_id')
    credential = CredentialSerializer()
