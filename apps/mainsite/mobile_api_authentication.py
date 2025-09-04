import logging
import urllib.error
import urllib.parse
import urllib.request
from allauth.socialaccount.models import SocialAccount
import requests
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from rest_framework.authentication import BaseAuthentication

from badgeuser.models import BadgeUser


class TemporaryUser:

    def __init__(self, user_payload, bearer_token):
        # Not saved to DB
        self.user_payload = user_payload
        self.bearer_token = bearer_token


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

        bearer_token = authorization[len('bearer '):]
        if not bearer_token:
            logger.info('MobileAPIAuthentication: return None as no bearer_token in authorization')
            return None

        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        url = f'{settings.EDUID_PROVIDER_URL}/introspect'
        auth = (settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET)
        response = requests.post(url, data=urllib.parse.urlencode({'token': bearer_token}), auth=auth, headers=headers,
                                 timeout=60)
        if response.status_code != 200:
            logger.info(f'MobileAPIAuthentication bad response from oidcng: {response.status_code} {response.json()}')
            return None

        introspect_json = response.json()
        logger.info(f'MobileAPIAuthentication introspect {introspect_json}')

        if not introspect_json['active']:
            logger.info(f'MobileAPIAuthentication inactive introspect_json {introspect_json}')
            return None
        if not 'eduid' in introspect_json:
            logger.info(f'MobileAPIAuthentication return None as no eduid in introspect_json {introspect_json}')
            return None

        social_account = SocialAccount.objects.filter(uid=introspect_json['eduid']).first()
        login_endpoint = request.path == "/mobile/api/login"
        if social_account is None:
            if login_endpoint:
                # further logic is dealt with in /mobile/api/login
                request.mobile_api_call = True
                return TemporaryUser(introspect_json, bearer_token), bearer_token
            else:
                # If not heading to login-endpoint, we return None resulting in 403
                return None
        # SocialAccount always has a User
        user = social_account.user
        if login_endpoint:
            # further logic is dealt with in /mobile/api/login
            request.mobile_api_call = True
            return user
        elif not user.general_terms_accepted() or not user.validated_name:
            # If not heading to login-endpoint, we return None resulting in 403
            return None

        request.mobile_api_call = True
        return user, bearer_token
