# api.py -- defines viewsets for models defined in badgeanalysis

from badgeanalysis.models import OpenBadge
from rest_framework import viewsets
from badgeanalysis.serializers import BadgeSerializer

class BadgeViewSet(viewsets.ModelViewSet):
    queryset = OpenBadge.objects.all()
    serializer_class = BadgeSerializer


##
#
# Useful views of information about badges
#
##

## Assertions
# Get a common set of information about a badge without revealing the hashed earner identifier
def anonymous_earner_information(badge):
    pass
    # TODO Implement


# Information about the assertion including the unobfuscated earner identifier
def identified_earner_information(badge):
    pass
    #TODO Implement
