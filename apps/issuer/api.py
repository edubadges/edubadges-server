# Views for Issuer API endpoints (incoming requests to this application)
from rest_framework import viewsets
from models import EarnerNotification
from serializers import EarnerNotificationSerializer


class EarnerNotificationViewSet(viewsets.ModelViewSet):
    queryset = EarnerNotification.objects.all()
    serializer_class = EarnerNotificationSerializer
