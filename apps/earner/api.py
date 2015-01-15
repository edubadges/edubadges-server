# Views for Earner API endpoints. Earners collect, annotate, share and export badges.
from django.contrib.auth import get_user_model

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
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (IsOwner,)

    def get(self, request):
        """
        return a list of earned badges in the requesting user's account
        """
        import pdb; pdb.set_trace();
        # TODO Use request.user
        try:
            user_badges = EarnerBadge.objects.filter(earner=1)
        except EarnerBadge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EarnerBadgeSerializer(user_badges, many=True)

        return Response(serializer.data)

    def post(self, request):
        import pdb; pdb.set_trace();
        """
        Add a new badge to an earner's collection
        request.data: {
            "badge_input": "http://assertionUrl? or assertion json text blob"
            "image": <File object?>
            "earner_description": "Some optional text"
        }
        Must have (either badge_input or image) and request.user
        """
        if not isinstance(request.user, get_user_model()):
            #TODO change this to 401 unauthenticated
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            the_actual_badge = OpenBadge(
                badge_input=request.data.get('badge_input', None),
                recipient_input=request.data.get('recipient_input', request.user.email),
                image=request.data.get('image', None)
            )
            the_actual_badge.save()
        except Exception as e:
            raise e

        try:
            new_earner_badge = EarnerBadge(
                earner=request.user,
                earner_description=request.data.get('earner_description', ''),
                earner_accepted=True,
                badge=the_actual_badge
            )
        except ValueError as e:
            return Response(status=status.HTTP_403_FORBIDDEN)

        

        try:
            new_earner_badge.save()
        except Exception as e:
            raise e

        serializer = EarnerBadgeSerializer(new_earner_badge)
        return Response(serializer.data)


class EarnerBadgeDetail(APIView):
    """
    View a single EarnerBadge in detail (GET) or update a single EarnerBadge with PUT
    """

    def get(self, request, pk):
        pass

    def put(self, resuest, pk):
        pass
