# Views for Earner API endpoints. Earners collect, annotate, share and export badges.
from rest_framework import authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from models import EarnerBadge
from badgeanalysis.models import OpenBadge
from serializers import EarnerBadgeSerializer
from mainsite.permissions import IsOwner


class EarnerBadgesList(APIView):
    """
    GET: Viewing a list of earners' badges. (and their annotations) or POST to create a new one
    """
    model = EarnerBadge

    # TODO: rich authentication possibilitiesfor remote API clients
    # authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (IsOwner,)

    def get(self, request):
        """
        return a list of earned badges in the requesting user's account
        """
        # TODO Use request.user
        try:
            user_badges = EarnerBadge.objects.filter(earner=1)
        except EarnerBadge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EarnerBadgeSerializer(user_badges, many=True)

        return Response(serializer.data)

    def post(self, request):
        """
        Add a new badge to an earner's collection
        request.data: {
            "badge_input": "http://assertionUrl? or assertion json text blob"
            "image": <File object?>
            "earner_description": "Some optional text"
        }
        Must have (either badge_input or image) and request.user
        """

        # TODO: use request.user
        new_earner_badge = EarnerBadge(earner=1, earner_description=request.data['earner_description'])
        new_earner_badge.badge = OpenBadge(
            badge_input=request.data['badge_input'],
            recipient_input=request.data['recipient_input'],
            image=request.data['image']
        )

        new_earner_badge.save()

        return Response(new_earner_badge)


class EarnerBadgeDetail(APIView):
    """
    View a single EarnerBadge in detail (GET) or update a single EarnerBadge with PUT
    """

    def get(self, request, pk):
        pass

    def put(self, resuest, pk):
        pass
