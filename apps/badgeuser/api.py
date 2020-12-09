import datetime

from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import url_str_to_user_pk
from apispec_drf.decorators import apispec_get_operation, apispec_delete_operation, apispec_list_operation
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import ProtectedError
from django.http import Http404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.exceptions import ErrorDetail
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer, ValidationError
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_302_FOUND, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from rest_framework.views import APIView

from badgeuser.models import BadgeUser, CachedEmailAddress, BadgrAccessToken, UserProvisionment, Terms, TermsAgreement
from badgeuser.permissions import BadgeUserIsAuthenticatedUser
from badgeuser.serializers import BadgeUserProfileSerializer, BadgeUserTokenSerializer, UserProvisionmentSerializer, \
    UserProvisionmentSerializerForEdit, TermsAgreementSerializer, TermsSerializer
from badgeuser.tasks import process_email_verification
from entity.api import BaseEntityDetailView, BaseEntityListView
from issuer.permissions import BadgrOAuthTokenHasScope
from mainsite.exceptions import BadgrApiException400, BadgrValidationError
from mainsite.models import BadgrApp
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.permissions import HasObjectPermission

RATE_LIMIT_DELTA = datetime.timedelta(minutes=5)


class BadgeUserDetail(BaseEntityDetailView):
    model = BadgeUser
    v1_serializer_class = BadgeUserProfileSerializer
    permission_classes = (BadgeUserIsAuthenticatedUser,)
    http_method_names = ('get', 'delete')

    def get_object(self, request, **kwargs):
        if request.user.is_authenticated:
            self.object = request.user
            self.has_object_permissions(request, self.object)
            return self.object
        raise BadgrApiException400("You do not have permission", 100)

    def delete(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        try:
            obj.delete()
        except ProtectedError as e:
            raise BadgrApiException400(error_message=e.args[0], error_code=999)
        return Response(status=HTTP_204_NO_CONTENT)


class BadgeUserToken(BaseEntityDetailView):
    model = BadgeUser
    permission_classes = (BadgeUserIsAuthenticatedUser,)
    v1_serializer_class = BadgeUserTokenSerializer

    def get_object(self, request, **kwargs):
        return request.user

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
        CachedEmailAddress.objects \
            .filter(email__iexact=emailconfirmation.email_address.email) \
            .exclude(pk=emailconfirmation.email_address.pk) \
            .delete()

        email_address.verified = True
        email_address.save()

        process_email_verification.delay(email_address.pk)

        redirect_url = badgrapp.ui_connect_success_redirect

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


class UserCreateProvisionment(BaseEntityListView):
    """
    Endpoint used for provisioning
    POST to create a provisionment for another
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = UserProvisionmentSerializer
    http_method_names = ['post']

    def post(self, request, **kwargs):
        context = self.get_context_data(**kwargs)
        response = []
        if not request.data:
            raise BadgrApiException400('No provisionments sent', 0)
        for provisionment in request.data:
            serializer = self.v1_serializer_class(data=provisionment, context=context)
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save(created_by=request.user)
                message = {'status': 'success',
                           'message': serializer.data}
            except ValidationError as e:
                if not isinstance(e, BadgrValidationError) and 'email' in e.detail:
                    # Consistency with other BadgrValidationErrors
                    e = BadgrValidationError("Enter a valid email address", 509)
                # check if email address was a duplicate
                duplicate_with_success = [x for x in response if x['status'] == 'success' and x['email'] == provisionment['email']]
                if duplicate_with_success:
                    e = BadgrValidationError('You entered this email address multiple times.', 510)
                message = {'status': 'failure',
                           'message': e.detail}
            message['email'] = provisionment['email']
            response.append(message)
        return Response(response, status=status.HTTP_201_CREATED)


class UserProvisionmentDetail(BaseEntityDetailView):
    """
    Endpoint used for provisioning
    PUT to edit a provisionment for another'
    DELETE to remove a provisionment for another'
    """
    model = UserProvisionment
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = UserProvisionmentSerializerForEdit
    http_method_names = ['put', 'delete']
    permission_map = {'PUT': 'may_administrate_users', 'DELETE': 'may_administrate_users'}


class AcceptProvisionmentDetail(BaseEntityDetailView):
    """
    Endpoint used for provisioning
    POST to accept or deny your own provisionment'
    """
    model = UserProvisionment
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    v1_serializer_class = UserProvisionmentSerializer
    http_method_names = ['post']

    def post(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):  # checks if obj is owned by request.user
            return Response(status=HTTP_404_NOT_FOUND)
        if request.data.get('accept', None):
            obj.accept()
        else:
            obj.reject()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj)
        return Response(serializer.data)


class AcceptTermsView(APIView):
    """
    Endpoint used for accepting terms
    POST to accept terms
    """
    model = Terms
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post', 'delete']

    def post(self, request, **kwargs):
        if request.data:
            serializer = TermsAgreementSerializer(data=request.data,
                                                  many=True,
                                                  context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)
        raise BadgrApiException400('Cannot accept terms, no data sent')

    def delete(self, request, **kwargs):
        if request.data:
            term_agreement = TermsAgreement.objects.get(entity_id=request.data['terms_agreement_entity_id'])
            term_agreement.agreed = False
            term_agreement.save()
            request.user.remove_cached_data(['cached_terms_agreements'])
            return Response(status=HTTP_200_OK)
        raise BadgrApiException400('Cannot revoke consent, no data sent', 999)

class PublicTermsView(APIView):
    """
    Public endpoint used for getting general terms
    GET to get terms
    """
    model = Terms
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['get']

    def get(self, request, **kwargs):
        user_type = kwargs.get('user_type', None)
        data = []
        if user_type == 'student':
            data = list(Terms.objects.filter(terms_type__in=(Terms.TYPE_SERVICE_AGREEMENT_STUDENT,
                                                             Terms.TYPE_TERMS_OF_SERVICE)))
        elif user_type == 'teacher':
            data = list(Terms.objects.filter(terms_type__in=(Terms.TYPE_SERVICE_AGREEMENT_EMPLOYEE,
                                                             Terms.TYPE_TERMS_OF_SERVICE)))
        if data:
            return Response(TermsSerializer(many=True).to_representation(data), status=HTTP_200_OK)
        else:
            return Response(status=HTTP_404_NOT_FOUND)
