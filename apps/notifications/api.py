from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from mainsite.permissions import TeachPermission


class NotificationsView(APIView):
    permission_classes = (TeachPermission,)

    def get(self, request, **kwargs):
        user = request.user
        return Response({}, status=status.HTTP_200_OK)

    def put(self, request, **kwargs):
        user = request.user
        lang = request.data.get('lang', 'en')
        # TODO, remove everything and re-create with the notifications in the data
        return Response({}, status=status.HTTP_200_OK)
