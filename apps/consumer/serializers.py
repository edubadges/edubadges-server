from rest_framework import serializers

from rest_framework.exceptions import ValidationError
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge
from badgeanalysis.serializers import BadgeSerializer


class ConsumerBadgeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    badge = BadgeSerializer()
