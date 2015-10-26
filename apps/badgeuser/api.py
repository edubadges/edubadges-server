from rest_framework import authentication, permissions, status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from mainsite.permissions import IsRequestUser

from .models import BadgeUser
from .serializers import TokenSerializer, BadgeUserSerializer


class BadgeUserDetail(generics.RetrieveUpdateAPIView):
    """
    View a single user profile by username
    """
    queryset = BadgeUser.objects.all()
    serializer_class = BadgeUserSerializer
    lookup_field = 'pk'

    # TODO: rich authentication possibilitiesfor remote API clients
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (IsRequestUser,)

    def get(self, request, user_id):
        """
        Return full details on a single badge the consumer is currently analyzing.
        """
        user = self.get_object()

        serializer = BadgeUserSerializer(user)

        return Response(serializer.data)

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
