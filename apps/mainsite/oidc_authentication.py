import logging
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
        logger = logging.getLogger('Badgr.Debug')
        x_requested_with = request.META.get("HTTP_X_REQUESTED_WITH")
        if x_requested_with and x_requested_with.lower() == "client":
            logger.info("Skipping OIDCAuthentication as HTTP_X_REQUESTED_WITH = client")
            return None

        logger.info(f"OIDCAuthentication {request.META}")
        authorization = request.environ.get('HTTP_AUTHORIZATION')
        if not authorization:
            logger.info("OIDCAuthentication no authorization")
            return None

        bearer_token = authorization[len('bearer '):]
        if not bearer_token:
            logger.info("OIDCAuthentication no bearer_token")
            return None

        payload = {'token': bearer_token}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        url = f"{settings.EDUID_PROVIDER_URL}/introspect"
        response = requests.post(url,
                                 data=urllib.parse.urlencode(payload),
                                 auth=(settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET),
                                 headers=headers)
        if response.status_code != 200:
            logger.info(f"OIDCAuthentication bad response {response.status_code} {response.json()}")
            return None

        introspect_json = response.json()
        logger.info(f"OIDCAuthentication introspect {introspect_json}")

        if not introspect_json['active']:
            return None
        user = None
        if 'email' in introspect_json:
            user = BadgeUser.objects.get(email=introspect_json['email'], is_teacher=True)
        elif 'client_id' in introspect_json:
            client_id = introspect_json['client_id']
            institution = Institution.objects.get(manage_client_id=client_id)
            logger.info(f"OIDCAuthentication institution {institution} client_id {client_id}")

            if institution and institution.sis_integration_enabled:
                user = institution.sis_default_user
        if user:
            request.sis_api_call = True

        return user, bearer_token
