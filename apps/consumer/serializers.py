from rest_framework import serializers

from rest_framework.exceptions import ValidationError
from models import ConsumerBadge
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge
from badgeanalysis.serializers import BadgeSerializer


class ConsumerBadgeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    consumer = serializers.CharField(max_length=128)
    badge = BadgeSerializer()
