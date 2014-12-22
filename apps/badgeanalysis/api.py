# api.py -- defines viewsets for models defined in badgeanalysis

from badgeanalysis.models import OpenBadge
from rest_framework import viewsets
from badgeanalysis.serializers import BadgeSerializer

class BadgeViewSet(viewsets.ModelViewSet):
    queryset = OpenBadge.objects.all()
    serializer_class = BadgeSerializer