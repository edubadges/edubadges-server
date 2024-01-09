from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.models import BadgeInstance
from mainsite.permissions import TeachPermission


class CredentialsView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        badge_id = request.data.get('badge_id')
        badge_instance = BadgeInstance.objects.get(id=badge_id)
        if badge_instance.user != request.user:
            raise Http404

        return Response(res, status=status.HTTP_200_OK)


class OffersView(APIView):
    permission_classes = (TeachPermission,)

    def post(self, request, **kwargs):
        badge_id = request.data.get('badge_id')
        badge_instance = BadgeInstance.objects.get(id=badge_id)
        if badge_instance.user != request.user:
            raise Http404
        # POST to ob3 endpoint and return the results

        return Response(res, status=status.HTTP_200_OK)
