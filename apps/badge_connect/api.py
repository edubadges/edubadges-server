import urllib.error
import urllib.parse
import urllib.request

import requests
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from issuer.models import BadgeInstance


class BadgeConnectView(GenericAPIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, **kwargs):
        authorization = request.environ.get("HTTP_AUTHORIZATION")
        if not authorization:
            raise PermissionDenied()
        bearer_token = authorization[len("bearer ") :]
        if not bearer_token:
            raise PermissionDenied()

        payload = {"token": bearer_token}
        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        url = f"{settings.EDUID_PROVIDER_URL}/introspect"
        response = requests.post(
            url,
            data=urllib.parse.urlencode(payload),
            auth=(settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET),
            headers=headers,
        )
        if response.status_code != 200:
            raise PermissionDenied()

        introspect_json = response.json()
        if not introspect_json["active"]:
            raise PermissionDenied()
        email = introspect_json["email"]
        badge_instance = BadgeInstance.objects.get(user__email=email, entity_id=kwargs.get("entity_id"))
        if not badge_instance.public or badge_instance.revoked:
            raise Http404

        return Response({"validated": True}, status=status.HTTP_200_OK)
