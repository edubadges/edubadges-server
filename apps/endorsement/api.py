import threading

from rest_framework.response import Response
from rest_framework.views import APIView
from endorsement.models import Endorsement
from endorsement.serializer import EndorsementSerializer
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite.exceptions import BadgrValidationError
from mainsite.permissions import AuthenticatedWithVerifiedEmail, TeachPermission
from mainsite.utils import EmailMessageMaker, send_mail
from rest_framework import status

# Send notifications to all users who have indicated they want to get notified
from notifications.models import BadgeClassUserNotification


def send_notifications(endorsement: Endorsement, current_user):
    user_notifications = BadgeClassUserNotification.objects.filter(badgeclass=endorsement.endorser).all()
    for user_notification in user_notifications:
        perms = endorsement.endorser.get_permissions(user_notification.user)
        if perms['may_award']:
            html_message = EmailMessageMaker.create_endorsement_requested_mail(current_user,
                                                                               user_notification.user,
                                                                               endorsement)
            send_mail(subject='Een endorsement is aangevraagd! An endorsement is requested!',
                      message=None, html_message=html_message,
                      recipient_list=[user_notification.user.email])
        else:
            user_notification.delete()


class EndorsementList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        serializer = EndorsementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            endorsement = serializer.save()
            thread = threading.Thread(target=send_notifications, args=(endorsement, request.user))
            thread.start()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EndorsementDetail(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['delete', 'put']
    permission_map = {'PUT': 'may_award'}
    model = Endorsement

    def put(self, request, **kwargs):
        endorsement = Endorsement.objects.get(entity_id=kwargs['entity_id'])
        user = request.user
        endorser_permissions = endorsement.endorser.get_permissions(user)
        endorsee_permissions = endorsement.endorsee.get_permissions(user)
        if not endorser_permissions['may_award'] and not endorsee_permissions['may_award']:
            raise BadgrValidationError('Insufficient permission', 999)
        new_status = request.data['status']
        endorsement.status = new_status
        if new_status == Endorsement.STATUS_REVOKED:
            revocation_reason = request.data['revocation_reason']
            endorsement.revocation_reason = revocation_reason
        elif new_status == Endorsement.STATUS_ACCEPTED:
            EmailMessageMaker.reject_approve_endorsement_mail(request.user, endorsement, True)
        elif new_status == Endorsement.STATUS_REJECTED:
            rejection_reason = request.data['rejection_reason']
            endorsement.rejection_reason = rejection_reason
            EmailMessageMaker.reject_approve_endorsement_mail(request.user, endorsement, False)
        endorsement.save()
        endorsement.endorsee.remove_cached_data(['cached_endorsements'])
        endorsement.endorser.remove_cached_data(['cached_endorsed'])
        return Response({}, status=status.HTTP_200_OK)

    def delete(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.endorsee.remove_cached_data(['cached_endorsements'])
        obj.endorser.remove_cached_data(['cached_endorsed'])
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class EndorsementResend(APIView):
    permission_classes = (TeachPermission,)
    permission_map = {'POST': 'may_award'}

    def post(self, request, **kwargs):
        endorsement = Endorsement.objects.get(entity_id=kwargs['entity_id'])
        thread = threading.Thread(target=send_notifications, args=(endorsement, request.user))
        thread.start()
        return Response({}, status=status.HTTP_200_OK)
