from rest_framework import serializers

from endorsement.models import Endorsement
from issuer.serializers import BadgeClassSlugRelatedField
from mainsite.exceptions import BadgrValidationError


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
        badge_class = validated_data['endorsee']
        user = self.context['request'].user
        permissions = badge_class.get_permissions(user)
        if not permissions['may_update']:
            raise BadgrValidationError('Insufficient permission', 999)
        endorsement = Endorsement(**validated_data)
        endorsement.created_by = user
        endorsement.save()
        badge_class.remove_cached_data(['cached_endorsements'])
        endorsement.endorser.remove_cached_data(['cached_endorsed'])
        return endorsement
