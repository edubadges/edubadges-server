import urllib.error
import urllib.parse
import urllib.request

import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication

from badgeuser.models import BadgeUser
from institution.models import Institution


class OIDCAuthentication(BaseAuthentication):

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        x_requested_with = request.META.get("HTTP_X_REQUESTED_WITH")
        if x_requested_with and x_requested_with.lower() == "client":
            return None

        authorization = request.environ.get('HTTP_AUTHORIZATION')
        if not authorization:
            return None
        bearer_token = authorization[len('bearer '):]
        if not bearer_token:
            return None

        payload = {'token': bearer_token}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        url = f"{settings.EDUID_PROVIDER_URL}/introspect"
        response = requests.post(url,
                                 data=urllib.parse.urlencode(payload),
                                 auth=(settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET),
                                 headers=headers)
        if response.status_code != 200:
            return None

        introspect_json = response.json()
        if not introspect_json['active']:
            return None
        user = None
        if 'email' in introspect_json:
            user = BadgeUser.objects.get(email=introspect_json['email'], is_teacher=True)
        elif 'client_id' in introspect_json:
            client_id = introspect_json['client_id']
            institution = Institution.objects.get(manage_client_id=client_id)
            if institution and institution.sis_integration_enabled:
                user = institution.sis_default_user
        if user:
            request.sis_api_call = True

        return user, bearer_token
