from rest_framework import serializers

from rest_framework.exceptions import ValidationError
from models import EarnerBadge
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge
from badgeanalysis.serializers import BadgeSerializer

class EarnerBadgeSerializer(serializers.Serializer):
    # TODO: how do you incorporate another serializer's output for a foreign key?
    # badge = serializers. ???
    earner = serializers.CharField(max_length=128)
    email = serializers.CharField(max_length=254)
    badge = BadgeSerializer()