from rest_framework import authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from mainsite.permissions import IsOwner

from .models import BadgeUser
from .serializers import TokenSerializer


class BadgeUserList(APIView):
    """
    GET a list of users on the system. Restricted to system administrators.
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
        View a list of users viewable in current scope
        """
        raise ValidationError("viewing a user list not implemented")


class BadgeUserDetail(APIView):
    """
    View a single user profile by username
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


class BadgeUserToken(APIView):
    model = BadgeUser

    authentication_classes = (
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get the authenticated user's auth token.
        A new auth token will be created if none already exist for this user.
        This request must be authenticated by a method other than TokenAuthentication.
        """
        token_input = {'username': request.user.username, 'replace': False}
        serializer = TokenSerializer(data=token_input)
        if serializer.is_valid():
            token_input['token'] = serializer.save()
        else:
            return Response("Could not validate token request", status=status.HTTP_400_BAD_REQUEST)

        return Response(token_input, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Invalidate the old token (if it exists) and create a new one.
        """
        token_input = {
            'username': request.user.username,
            'replace': True
        }
        serializer = TokenSerializer(data=token_input)

        if serializer.is_valid():
            token_input['token'] = serializer.save()
        else:
            return Response("Could not validate token request", status=status.HTTP_400_BAD_REQUEST)

        return Response(token_input, status=status.HTTP_201_CREATED)
