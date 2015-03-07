from rest_framework import serializers
from badgeanalysis.serializers import BadgeSerializer, BadgeDetailSerializer


class ConsumerBadgeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    badge = BadgeSerializer()


class ConsumerBadgeDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    badge = BadgeDetailSerializer()
