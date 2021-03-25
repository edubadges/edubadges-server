from rest_framework import serializers

from directaward.models import DirectAward
from issuer.serializers import BadgeClassSlugRelatedField
from mainsite.exceptions import BadgrValidationError


class DirectAwardSerializer(serializers.Serializer):

    class Meta:
        model = DirectAward

    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=False)
    eppn = serializers.CharField(required=False)
    recipient_email = serializers.EmailField(required=False)

    def create(self, validated_data):
        user_permissions = validated_data['badgeclass'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            return DirectAward.objects.create(**validated_data)
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance


