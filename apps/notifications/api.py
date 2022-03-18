from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.models import BadgeClass
from mainsite.permissions import TeachPermission
from notifications.models import BadgeClassUserNotification


class NotificationsView(APIView):
    permission_classes = (TeachPermission,)

    def put(self, request, **kwargs):
        user = request.user
        deletions = request.data.get('deletions')
        creations = request.data.get('creations')
        BadgeClassUserNotification.objects.filter(badgeclass__entity_id__in=[d['entity_id'] for d in deletions]).delete()
        for c in creations:
            BadgeClassUserNotification.objects.create(
                user=user,
                badgeclass=BadgeClass.objects.get(entity_id=c['entity_id'])
            )
        return Response({}, status=status.HTTP_200_OK)
