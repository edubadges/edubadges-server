import datetime

from django.db.models import ProtectedError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from rest_framework.views import APIView

from badgeuser.models import BadgeUser, UserProvisionment, Terms, TermsAgreement
from badgeuser.permissions import BadgeUserIsAuthenticatedUser, InstitutionAdmin
from badgeuser.serializers import BadgeUserProfileSerializer, UserProvisionmentSerializer, \
    UserProvisionmentSerializerForEdit, TermsAgreementSerializer, TermsSerializer
from directaward.models import DirectAwardBundle
from entity.api import BaseEntityDetailView, BaseEntityListView
from mainsite.exceptions import BadgrApiException400, BadgrValidationError
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


class UserDeleteView(BaseEntityDetailView):
    permission_classes = (InstitutionAdmin,)
    http_method_names = ['delete']
    model = BadgeUser

    def delete(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        awards_issued = DirectAwardBundle.objects.filter(created_by=obj).count() > 0
        if request.user.institution != obj.institution or awards_issued:
            return Response(status=HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)
