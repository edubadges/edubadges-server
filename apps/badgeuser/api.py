from rest_framework import authentication, permissions, status, generics
from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from mainsite.permissions import IsRequestUser

from .models import BadgeUser
from .serializers import BadgeUserSerializer, BadgeUserProfileSerializer


class BadgeUserDetail(generics.RetrieveUpdateAPIView):
    """
    View another user's profile by username. Currently permissions only allow you to view your own profile.
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
        Return public profile information on another user.
        """
        user = self.get_object()

        serializer = BadgeUserSerializer(user)

        return Response(serializer.data)


class BadgeUserProfile(APIView):
    """
    View or update your own profile, or register a new account.
    """
    serializer_class = BadgeUserProfileSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):

        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        new_user = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        if request.user.is_anonymous():
            raise NotAuthenticated()

        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

    # def put(self, request):
    #     pass


class BadgeUserToken(APIView):
    model = BadgeUser
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get the authenticated user's auth token.
        A new auth token will be created if none already exist for this user.
        """
        token_input = {
            'username': request.user.username,
            'token': request.user.cached_token()
        }
        return Response(token_input, status=status.HTTP_200_OK)

    def put(self, request):
        """
        Invalidate the old token (if it exists) and create a new one.
        """
        token_input = {
            'username': request.user.username,
            'token': request.user.replace_token(),
            'replace': True
        }
        request.user.save()

        return Response(token_input, status=status.HTTP_201_CREATED)
