from rest_framework.response import Response
from rest_framework import status

from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from directaward.serializer import DirectAwardSerializer, DirectAwardBundleSerializer
from directaward.models import DirectAward
from directaward.permissions import IsDirectAwardOwner
from mainsite.exceptions import BadgrValidationError, BadgrValidationFieldError, BadgrApiException400
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.permissions import HasObjectPermission


class DirectAwardBundleList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = DirectAwardBundleSerializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}


class DirectAwardRevoke(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    def post(self, request, **kwargs):
        """
        Revoke direct awards
        """
        revocation_reason = request.data.get('revocation_reason', None)
        direct_awards = request.data.get('direct_awards', None)
        if not revocation_reason:
            raise BadgrValidationFieldError('revocation_reason', "This field is required", 999)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', "This field is required", 999)
        cache_cleared = False;
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award['entity_id'])
            if direct_award.get_permissions(request.user)['may_award']:
                direct_award.revoke(revocation_reason)
                if not cache_cleared:
                    direct_award.badgeclass.remove_cached_data(['cached_direct_awards'])
                    cache_cleared = True
            else:
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result":"ok"}, status=status.HTTP_200_OK)


class DirectAwardDetail(BaseEntityDetailView):
    model = DirectAward
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = DirectAwardSerializer
    http_method_names = ['put']
    permission_map = {'PUT': 'may_award'}


class DirectAwardAccept(BaseEntityDetailView):
    model = DirectAward  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsDirectAwardOwner)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        directaward = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, directaward):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get('accept', False):  # has accepted it
            if not directaward.badgeclass.terms_accepted(request.user):
                raise BadgrValidationError("Cannot accept direct award, must accept badgeclass terms first", 999)
            assertion = directaward.award(recipient=request.user)
            directaward.badgeclass.remove_cached_data(['cached_direct_awards'])
            directaward.delete()
            return Response({'entity_id': assertion.entity_id}, status=status.HTTP_201_CREATED)
        elif not request.data.get('accept', True):  # has rejected it
            directaward.status = DirectAward.STATUS_REJECTED  # reject it
            directaward.save()
            directaward.badgeclass.remove_cached_data(['cached_direct_awards'])
            return Response({'rejected': True}, status=status.HTTP_200_OK)
        raise BadgrValidationError('Neither accepted or rejected the direct award', 999)
