import datetime

from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import url_str_to_user_pk
from apispec_drf.decorators import apispec_get_operation, apispec_put_operation, apispec_delete_operation, apispec_list_operation
from badgeuser.models import BadgeUser, CachedEmailAddress, BadgrAccessToken
from badgeuser.permissions import BadgeUserIsAuthenticatedUser
from badgeuser.serializers_v1 import BadgeUserProfileSerializerV1, BadgeUserTokenSerializerV1
from badgeuser.tasks import process_email_verification
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils import timezone
from entity.api import BaseEntityDetailView, BaseEntityListView
from issuer.permissions import BadgrOAuthTokenHasScope
from mainsite.models import BadgrApp
from rest_framework import permissions
from rest_framework.exceptions import ValidationError as RestframeworkValidationError
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.status import HTTP_302_FOUND, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED

RATE_LIMIT_DELTA = datetime.timedelta(minutes=5)


class BadgeUserDetail(BaseEntityDetailView):
    model = BadgeUser
    v1_serializer_class = BadgeUserProfileSerializerV1
    permission_classes = (permissions.AllowAny, BadgrOAuthTokenHasScope)
    valid_scopes = {
        "post": ["*"],
        "get": ["r:profile", "rw:profile"],
        "put": ["rw:profile"],
    }

    def post(self, request, **kwargs):
        """
        Signup for a new account
        """
        if request.version == 'v1':
            serializer_cls = self.get_serializer_class()
            serializer = serializer_cls(
                data=request.data, context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            try:
                new_user = serializer.save()
            except DjangoValidationError as e:
                raise RestframeworkValidationError(e.message)
            return Response(serializer.data, status=HTTP_201_CREATED)

        return Response(status=HTTP_404_NOT_FOUND)

    @apispec_get_operation('BadgeUser',
        summary="Get a single BadgeUser profile",
        description="Use the entityId 'self' to retrieve the authenticated user's profile",
        tags=['BadgeUsers']
    )
    def get(self, request, **kwargs):
        return super(BadgeUserDetail, self).get(request, **kwargs)

    @apispec_put_operation('BadgeUser',
        summary="Update a BadgeUser",
        description="Use the entityId 'self' to update the authenticated user's profile",
        tags=['BadgeUsers']
    )
    def put(self, request, **kwargs):
        return super(BadgeUserDetail, self).put(request, allow_partial=True, **kwargs)

    def get_object(self, request, **kwargs):
        version = getattr(request, 'version', 'v1')
        if version == 'v2':
            entity_id = kwargs.get('entity_id')
            if entity_id == 'self':
                self.object = request.user
                return self.object
            try:
                self.object = BadgeUser.cached.get(entity_id=entity_id)
            except BadgeUser.DoesNotExist:
                pass
            else:
                return self.object
        elif version == 'v1':
            if request.user.is_authenticated:
                self.object = request.user
                return self.object
        raise Http404

    def has_object_permissions(self, request, obj):
        method = request.method.lower()
        if method == 'post':
            return True

        if isinstance(obj, BadgeUser):

            if method == 'get':
                if request.user.id == obj.id:
                    # always have access to your own user
                    return True
                # peers is obsolete
                # if obj in request.user.peers:
                #     # you can see some info about users you know about
                #     return True

            if method == 'put':
                # only current user can update their own profile
                return request.user.id == obj.id
        return False

    def get_context_data(self, **kwargs):
        context = super(BadgeUserDetail, self).get_context_data(**kwargs)
        context['isSelf'] = (self.object.id == self.request.user.id)
        return context


class BadgeUserToken(BaseEntityDetailView):
    model = BadgeUser
    permission_classes = (BadgeUserIsAuthenticatedUser,)
    v1_serializer_class = BadgeUserTokenSerializerV1

    def get_object(self, request, **kwargs):
        return request.user

    # deprecate from public API docs in favor of oauth2
    # @apispec_get_operation('BadgeUserToken',
    #     summary="Get the authenticated user's auth token",
    #     description="A new auth token will be created if none already exist for this user",
    #     tags=['Authentication'],
    # )
    def get(self, request, **kwargs):
        return super(BadgeUserToken, self).get(request, **kwargs)

    # deprecate from public API docs in favor of oauth2
    # @apispec_operation(
    #     summary="Invalidate the old token and create a new one",
    #     tags=['Authentication'],
    # )
    def put(self, request, **kwargs):
        request.user.replace_token()  # generate new token first
        self.token_replaced = True
        return super(BadgeUserToken, self).put(request, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(BadgeUserToken, self).get_context_data(**kwargs)
        context['tokenReplaced'] = getattr(self, 'token_replaced', False)
        return context


class BaseUserRecoveryView(BaseEntityDetailView):
    def _get_user(self, uidb36):
        User = get_user_model()
        try:
            pk = url_str_to_user_pk(uidb36)
            return User.objects.get(pk=pk)
        except (ValueError, User.DoesNotExist):
            return None

    def get_response(self, obj={}, status=HTTP_200_OK):
        context = self.get_context_data()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj, context=context)
        return Response(serializer.data, status=status)


class BadgeUserEmailConfirm(BaseUserRecoveryView):
    permission_classes = (permissions.AllowAny,)
    v1_serializer_class = BaseSerializer

    def get(self, request, **kwargs):
        """
        Confirm an email address
        """

        badgrapp_id = request.query_params.get('a', None)
        if badgrapp_id is None:
            badgrapp_id = getattr(settings, 'BADGR_APP_ID', 1)
        try:
            badgrapp = BadgrApp.objects.get(id=badgrapp_id)
        except BadgrApp.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        emailconfirmation = EmailConfirmationHMAC.from_key(kwargs.get('confirm_id'))
        if emailconfirmation is None:
            return Response(status=HTTP_404_NOT_FOUND)

        try:
            email_address = CachedEmailAddress.cached.get(pk=emailconfirmation.email_address.pk)
        except CachedEmailAddress.DoesNotExist:
            return Response(status=HTTP_404_NOT_FOUND)

        # We allow multiple users to add the same (unverified) email address.
        # A user can claim the address by verifying it.
        # If a user verifies an email address, all other users who had added that address will have that address deleted
        # same_email_addresses = CachedEmailAddress.objects\  TODO: refactor db to include variants
        #     .filter(email=emailconfirmation.email_address.email)\  TODO: refactor db to include variants
        #     .exclude(pk=emailconfirmation.email_address.pk)  TODO: refactor db to include variants
        all_email_addresses = CachedEmailAddress.objects.all()
        invalid_claimants_email_addresses = [
            ea for ea in all_email_addresses
            if ea.email.lower() == email_address.email.lower()
            and ea.pk != emailconfirmation.email_address.pk
        ]
        for _email_address in invalid_claimants_email_addresses:
            _email_address.delete()

        email_address.verified = True
        email_address.save()

        process_email_verification.delay(email_address.pk)

        redirect_url = badgrapp.ui_login_redirect

        return Response(status=HTTP_302_FOUND, headers={'Location': redirect_url})


class AccessTokenList(BaseEntityListView):
    model = BadgrAccessToken
    permission_classes = (permissions.IsAuthenticated, BadgrOAuthTokenHasScope)
    valid_scopes = ['rw:profile']

    def get_objects(self, request, **kwargs):
        return BadgrAccessToken.objects.filter(user=request.user, expires__gt=timezone.now())

    @apispec_list_operation('AccessToken',
        summary='Get a list of access tokens for authenticated user',
        tags=['Authentication']
    )
    def get(self, request, **kwargs):
        return super(AccessTokenList, self).get(request, **kwargs)


class AccessTokenDetail(BaseEntityDetailView):
    model = BadgrAccessToken
    permission_classes = (permissions.IsAuthenticated, BadgrOAuthTokenHasScope)
    valid_scopes = ['rw:profile']

    def get_object(self, request, **kwargs):
        self.object = BadgrAccessToken.objects.get_from_entity_id(kwargs.get('entity_id'))
        if not self.has_object_permissions(request, self.object):
            raise Http404
        return self.object

    @apispec_get_operation('AccessToken',
        summary='Get a single AccessToken',
        tags=['Authentication']
    )
    def get(self, request, **kwargs):
        return super(AccessTokenDetail, self).get(request, **kwargs)

    @apispec_delete_operation('AccessToken',
        summary='Revoke an AccessToken',
        tags=['Authentication']
    )
    def delete(self, request, **kwargs):
        return super(AccessTokenDetail, self).delete(request, **kwargs)


