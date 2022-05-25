from rest_framework import serializers

from endorsement.models import Endorsement
from issuer.serializers import BadgeClassSlugRelatedField


class EndorsementSerializer(serializers.Serializer):
    class Meta:
        model = Endorsement

    endorser = BadgeClassSlugRelatedField(slug_field='entity_id', required=True)
    endorsee = BadgeClassSlugRelatedField(slug_field='entity_id', required=True)
    claim = serializers.CharField(required=True)
    description = serializers.CharField(required=True)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    revocation_reason = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def create(self, validated_data):
        endorsement = Endorsement(**validated_data)
        endorsement.save()
        # endorsement.send_email()
        return endorsement

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance
