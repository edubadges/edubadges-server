# serializers.py - defines Django REST Framework serializers to be used with the API.
from rest_framework import serializers
from badgeanalysis.models import OpenBadge


class BadgeSerializer(serializers.Serializer):
    recipient_input = serializers.CharField(max_length=2048)
    image = serializers.CharField(max_length=512)
    full_badge_object = serializers.CharField(max_length=16384)