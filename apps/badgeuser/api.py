from rest_framework import authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from mainsite.permissions import IsOwner
from models import BadgeUser


class BadgeUserList(APIView):
    """
    GET: Viewing a list of a consumer' badges, or POST to upload a new one to analyze
    """
    model = BadgeUser

    # TODO: rich authentication possibilitiesfor remote API clients
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (IsOwner,)

    def get(self, request):
        """
        return a list of of badges that the consumer is currently analyzing.
        TODO: make these badges expire after a few days
        """
        raise ValidationError("viewing a user list not implemented")


class BadgeUserDetail(APIView):
    """
    View a single ConsumerBadge in detail (GET) or update a single ConsumerBadge with PUT
    """
    model = BadgeUser

    # TODO: rich authentication possibilitiesfor remote API clients
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (IsOwner,)

    def get(self, request, username):
        """
        Return full details on a single badge the consumer is currently analyzing.
        """
        raise ValidationError("viewing a single user not implemented")

    def put(self, resuest, pk):
        raise ValidationError("updating a single user not implemented")
