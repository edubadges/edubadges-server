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
        endorsement.endorsee.remove_cached_data(['cached_endorsements'])
        endorsement.endorser.remove_cached_data(['cached_endorsed'])
        # endorsement.send_email()
        return endorsement
