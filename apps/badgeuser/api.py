import re

from allauth.account.adapter import get_adapter
from allauth.account.utils import user_pk_to_url_str, url_str_to_user_pk
from allauth.utils import build_absolute_uri
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import get_current_site
from django.core.urlresolvers import reverse
from django.http import Http404
from rest_framework import permissions, status, generics
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from mainsite.models import BadgrApp
from mainsite.permissions import IsRequestUser
from .models import BadgeUser, CachedEmailAddress
from .serializers import BadgeUserProfileSerializer, ExistingEmailSerializer, NewEmailSerializer, \
    BadgeUserExistingProfileSerializer


class BadgeUserDetail(generics.RetrieveAPIView):
    """
    View user's profile. Currently permissions only allow you to view your own profile.
    """
    serializer_class = BadgeUserExistingProfileSerializer
    model = BadgeUser
    permission_classes = (IsRequestUser,)

    def get_object(self):
        try:
            obj = BadgeUser.cached.get(pk=self.kwargs.get('user_id'))
            self.check_object_permissions(self.request, obj)
            return obj
        except BadgeUser.DoesNotExist:
            raise Http404()


class BadgeUserProfile(APIView):
    serializer_class = BadgeUserProfileSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        """
        Signup for a new account
        ---
        serializer: BadgeUserProfileSerializer
        """
        serializer = self.serializer_class(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        new_user = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get(self, request):
        """
        Get the current user's profile
        ---
        serializer: BadgeUserProfileSerializer
        """
        if request.user.is_anonymous():
            raise NotAuthenticated()

        serializer = BadgeUserExistingProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        """
        Update the current user's profile
        ---
        serializer: BadgeUserExistingProfileSerializer
        """
        if request.user.is_anonymous():
            raise NotAuthenticated()

        serializer = BadgeUserExistingProfileSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


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



class BadgeUserEmailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_email(self, **kwargs):
        try:
            email_address = CachedEmailAddress.cached.get(**kwargs)
        except CachedEmailAddress.DoesNotExist:
            return None
        else:
            return email_address

class BadgeUserEmailDetail(BadgeUserEmailView):
    model = CachedEmailAddress

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
        email_address = self.get_email(pk=id)
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
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if email_address.primary:
            return Response(status=status.HTTP_400_BAD_REQUEST)

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
              required: false
            - name: resend
              type: boolean
              paramType: form
              description: Request the verification email be resent
              required: false
        """
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if email_address.verified:
            if request.data.get('primary'):
                email_address.set_as_primary()
                email_address.publish()
        else:
            if request.data.get('resend'):
                email_address.send_confirmation(request=request)

        serializer = ExistingEmailSerializer(email_address, context={'request': request})
        serialized = serializer.data
        return Response(serialized, status=status.HTTP_200_OK)


class BadgeUserForgotPassword(BadgeUserEmailView):
    permission_classes = ()

    def post(self, request):
        """
        Request an account recovery email.
        ---
        parameters:
            - name: email
              type: string
              paramType: form
              description: The email address on file to send recovery email
              required: true
        """

        email = request.data.get('email')
        email_address = self.get_email(email=email)
        if email_address is None:
            # return 200 here because we don't want to expose information about which emails we know about
            return Response(status=status.HTTP_200_OK)

        # taken from allauth.account.forms.ResetPasswordForm
        temp_key = default_token_generator.make_token(email_address.user)
        token = "{uidb36}-{key}".format(uidb36=user_pk_to_url_str(email_address.user),
                                        key=temp_key)
        badgr_app = BadgrApp.objects.get_current(request)
        reset_url = badgr_app.forgot_password_redirect + token

        email_context = {
            "site": get_current_site(request),
            "user": email_address.user,
            "password_reset_url": reset_url,
        }
        get_adapter().send_mail('account/email/password_reset_key', email, email_context)

        return Response(status=status.HTTP_200_OK)

    def put(self, request):
        """
        Recover an account and set a new password.
        ---
        parameters:
            - name: token
              type: string
              paramType: form
              description: The token received in the recovery email
              required: true
            - name: password
              type: string
              paramType: form
              description: The new password to use
              required: true
        """
        token = request.data.get('token')
        password = request.data.get('password')

        matches = re.search(r'([0-9A-Za-z]+)-(.*)', token)
        if not matches:
            return Response(status=status.HTTP_404_NOT_FOUND)
        uidb36 = matches.group(1)
        key = matches.group(2)
        if not (uidb36 and key):
            return Response(status=status.HTTP_404_NOT_FOUND)

        user = self._get_user(uidb36)
        if user is None or not default_token_generator.check_token(user, key):
            return Response(status=status.HTTP_404_NOT_FOUND)

        user.set_password(password)
        user.save()
        return Response(status=status.HTTP_200_OK)

    def _get_user(self, uidb36):
        User = get_user_model()
        try:
            pk = url_str_to_user_pk(uidb36)
            return User.objects.get(pk=pk)
        except (ValueError, User.DoesNotExist):
            return None


