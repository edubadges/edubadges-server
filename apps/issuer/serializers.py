from rest_framework import serializers
from models import EarnerNotification


class EarnerNotificationSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=2048)
    email = serializers.CharField(max_length=254)
