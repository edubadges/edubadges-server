from django.db import IntegrityError
from rest_framework import authentication, permissions, status, generics, serializers
from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from mainsite.permissions import IsRequestUser

from .models import BadgeUser, CachedEmailAddress
from .serializers import BadgeUserSerializer, BadgeUserProfileSerializer, ExistingEmailSerializer, NewEmailSerializer


class BadgeUserDetail(generics.RetrieveUpdateAPIView):
    """
    View another user's profile by username. Currently permissions only allow you to view your own profile.
    """
    queryset = BadgeUser.objects.all()
    serializer_class = BadgeUserSerializer
    lookup_field = 'pk'

    # TODO: rich authentication possibilities for remote API clients
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


class BadgeUserEmailList(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get a list of user's registered emails.
        ---
        serializer: ExistingEmailSerializer
        """
        instances = request.user.cached_emails()
        serializer = ExistingEmailSerializer(instances, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """
        Register a new unverified email.
        ---
        serializer: NewEmailSerializer
        parameters:
            - name: email
              description: The email to register
              required: true
              type: string
              paramType: form
        """
        serializer = NewEmailSerializer(data=request.data, context={'request: request'})
        serializer.is_valid(raise_exception=True)

        serializer.save(user=request.user)
        email = serializer.data

        # logger.event(badgrlog.UserAddedEmail())
        return Response(email, status=status.HTTP_201_CREATED)


class BadgeUserEmailDetail(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    mode = CachedEmailAddress

    def get_email(self, email_id):
        try:
            email_address = CachedEmailAddress.cached.get(pk=email_id)
        except CachedEmailAddress.DoesNotExist:
            return None
        else:
            return email_address

    def get(self, request, id):
        """
        Get detail for one registered email.
        ---
        serializer: ExistingEmailSerializer
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
        """
        email_address = self.get_email(id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != self.request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = ExistingEmailSerializer(email_address, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, id):
        """
        Remove a registered email for the current user.
        ---
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
        """
        email_address = self.get_email(id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        email_address.delete()
        return Response("Email '{}' has been deleted.".format(email_address.email), status.HTTP_200_OK)

    def put(self, request, id):
        """
        Update a registered email for the current user.
        serializer: ExistingEmailSerializer
        ---
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
            - name: primary
              type: boolean
              paramType: form
              description: Should this email be primary contact for the user
              required: true
        """
        email_address = self.get_email(id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = ExistingEmailSerializer(email_address, context={'request': request})

        if request.data.get('primary') and email_address.verified:
            email_address.set_as_primary()
        serialized = serializer.data
        return Response(serialized, status=status.HTTP_200_OK)

