import logging
import urllib.error
import urllib.parse
import urllib.request

import requests
from django.conf import settings
from django.core.exceptions import BadRequest
from rest_framework.authentication import BaseAuthentication

from badgeuser.models import BadgeUser
from institution.models import Institution


class MobileAPIAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        logger = logging.getLogger('Badgr.Debug')
        x_requested_with = request.headers.get('x-requested-with')
        if not x_requested_with or x_requested_with.lower() != 'mobile':
            logger.info('Skipping MobileAPIAuthentication as HTTP_X_REQUESTED_WITH is NOT mobile')
            return None

        logger.info(f'MobileAPIAuthentication {request.META}')
        authorization = request.environ.get('HTTP_AUTHORIZATION')
        if not authorization:
            logger.info('MobileAPIAuthentication: return None as no authorization header')
            return None

        bearer_token = authorization[len('bearer ') :]
        if not bearer_token:
            logger.info('MobileAPIAuthentication: return None as no bearer_token in authorization')
            return None

        payload = {'token': bearer_token}
        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        url = f'{settings.EDUID_PROVIDER_URL}/introspect'
        auth = (settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET)
        response = requests.post(url, data=urllib.parse.urlencode(payload), auth=auth, headers=headers, timeout=60)
        if response.status_code != 200:
            logger.info(f'MobileAPIAuthentication bad response from oidcng: {response.status_code} {response.json()}')
            return None

        introspect_json = response.json()
        logger.info(f'MobileAPIAuthentication introspect {introspect_json}')

        if not introspect_json['active']:
            logger.info(f'MobileAPIAuthentication inactive introspect_json {introspect_json}')
            return None
        if not 'email' in introspect_json:
            logger.info(f'MobileAPIAuthentication return None as no email in introspect_json {introspect_json}')
            return None

        user = BadgeUser.objects.get(email=introspect_json['email'], is_teacher=False)
        # TODO need to check if we need to add social data - see edubadges-server/apps/badgrsocialauth/providers/eduid/views.py
        if user:
            request.mobile_api_call = True

        return user, bearer_token
