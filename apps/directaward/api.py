import threading

from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, inline_serializer
from directaward.models import DirectAward
from directaward.permissions import IsDirectAwardOwner
from directaward.serializer import DirectAwardSerializer, DirectAwardBundleSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite import settings
from mainsite.exceptions import BadgrValidationError, BadgrValidationFieldError, BadgrApiException400
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail
from staff.permissions import HasObjectPermission
from rest_framework import serializers
import datetime

class DirectAwardBundleList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = DirectAwardBundleSerializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}


class DirectAwardRevoke(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    @extend_schema(
        request=inline_serializer(
            name="DirectAwardRevokeSerializer",
            fields={
                "revocation_reason": serializers.CharField(),
                "direct_awards": serializers.ListField(child=serializers.DictField(child=serializers.CharField()))
            },
        ),
    )
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
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award['entity_id'])
            if direct_award.get_permissions(request.user)['may_award']:
                direct_award.revoke(revocation_reason)
                direct_award.bundle.remove_cached_data(['cached_direct_awards'])
                direct_award.badgeclass.remove_cached_data(['cached_direct_awards'])
                direct_award.badgeclass.remove_cached_data(['cached_direct_award_bundles'])
            else:
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result": "ok"}, status=status.HTTP_200_OK)


class DirectAwardResend(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    @extend_schema(
        request=inline_serializer(
            name="DirectAwardResendSerializer",
            fields={
                "direct_awards": serializers.ListField(child=serializers.DictField(child=serializers.CharField()))
            },
        ),
    )
    def post(self, request, **kwargs):
        direct_awards = request.data.get('direct_awards', None)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', "This field is required", 999)
        successful_direct_awards = []
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award['entity_id'])
            direct_award.resend_at = datetime.datetime.now()
            direct_award.save()
            if direct_award.get_permissions(request.user)['may_award']:
                successful_direct_awards.append(direct_award)
            else:
                raise BadgrApiException400("You do not have permission", 100)

        def send_mail(awards):
            for da in awards:
                da.notify_recipient()

        thread = threading.Thread(target=send_mail, args=(successful_direct_awards,))
        thread.start()

        return Response({"result": "ok"}, status=status.HTTP_200_OK)


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
            directaward.bundle.remove_cached_data(['cached_direct_awards'])
            directaward.delete()
            return Response({'entity_id': assertion.entity_id}, status=status.HTTP_201_CREATED)
        elif not request.data.get('accept', True):  # has rejected it
            directaward.status = DirectAward.STATUS_REJECTED  # reject it
            directaward.save()
            directaward.badgeclass.remove_cached_data(['cached_direct_awards'])
            directaward.bundle.remove_cached_data(['cached_direct_awards'])
            return Response({'rejected': True}, status=status.HTTP_200_OK)
        raise BadgrValidationError('Neither accepted or rejected the direct award', 999)


class DirectAwardDelete(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['put']
    permission_map = {'PUT': 'may_award'}

    def put(self, request, **kwargs):
        direct_awards = request.data.get('direct_awards', None)
        revocation_reason = request.data.get('revocation_reason', None)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', "This field is required", 999)
        delete_at = datetime.datetime.utcnow() + datetime.timedelta(days=settings.DIRECT_AWARDS_DELETION_THRESHOLD_DAYS)
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award['entity_id'])
            if direct_award.get_permissions(request.user)['may_award']:
                direct_award.delete_at = delete_at
                direct_award.status = DirectAward.STATUS_DELETED
                direct_award.revocation_reason = revocation_reason
                direct_award.save()
                direct_award.badgeclass.remove_cached_data(['cached_direct_awards'])
                direct_award.bundle.remove_cached_data(['cached_direct_awards'])
                html_message = EmailMessageMaker.create_direct_award_deleted_email(direct_award)
                send_mail(subject='Awarded eduBadge has been deleted',
                          message=None,
                          html_message=html_message,
                          recipient_list=[direct_award.recipient_email])

            else:
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result": "ok"}, status=status.HTTP_200_OK)
