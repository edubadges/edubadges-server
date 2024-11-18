from django.utils import timezone
from rest_framework import serializers

from apps.mainsite.settings import UI_URL

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

class AchievementSerializer(serializers.Serializer):
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

class CredentialSerializer(serializers.Serializer):
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

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        """Remove a list of specific fields if they are None"""
        to_remove = ['validFrom', 'validUntil']
        for key in to_remove:
            if ret.get(key) is None:
                ret.pop(key)

        return ret

class EduCredentialSerializer(serializers.Serializer):
    offerId = serializers.CharField(source='offer_id')
    credentialConfigurationId = serializers.CharField(source='credential_configuration_id')
    credential = CredentialSerializer()
