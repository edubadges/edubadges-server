import logging
import urllib.error
import urllib.parse
import urllib.request

import requests
from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

GENERAL_TERMS_PATH = '/mobile/api/accept-general-terms'

API_LOGIN_PATH = '/mobile/api/login'


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
            logger.info('MobileAPIAuthentication: raise AuthenticationFailed as no authorization header')
            raise AuthenticationFailed('Authentication credentials were not provided.')

        bearer_token = authorization[len('bearer ') :]
        if not bearer_token:
            logger.info('MobileAPIAuthentication: raise AuthenticationFailed as no bearer_token in authorization')
            raise AuthenticationFailed('Authentication credentials were not provided.')

        bearer_token = authorization[len('bearer ') :]
        if not bearer_token:
            logger.info('MobileAPIAuthentication: return None as no bearer_token in authorization')
            return None

        headers = {'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
        url = f'{settings.EDUID_PROVIDER_URL}/introspect'
        auth = (settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET)
        response = requests.post(
            url, data=urllib.parse.urlencode({'token': bearer_token}), auth=auth, headers=headers, timeout=60
        )
        if response.status_code != 200:
            logger.info(f'MobileAPIAuthentication bad response from oidcng: {response.status_code} {response.json()}')
            raise AuthenticationFailed('Invalid authentication credentials.')

        introspect_json = response.json()
        logger.info(f'MobileAPIAuthentication introspect {introspect_json}')

        if not introspect_json['active']:
            logger.info(f'MobileAPIAuthentication inactive introspect_json {introspect_json}')
            raise AuthenticationFailed('Invalid authentication credentials.')
        if settings.EDUID_IDENTIFIER not in introspect_json:
            logger.info(
                f'MobileAPIAuthentication raise AuthenticationFailed as no {settings.EDUID_IDENTIFIER} in introspect_json {introspect_json}'
            )
            raise AuthenticationFailed('Invalid authentication credentials.')

        introspect_json = response.json()
        logger.info(f'MobileAPIAuthentication introspect {introspect_json}')

        if not introspect_json['active']:
            logger.info(f'MobileAPIAuthentication inactive introspect_json {introspect_json}')
            return None
        if settings.EDUID_IDENTIFIER not in introspect_json:
            logger.info(
                f'MobileAPIAuthentication return None as no {settings.EDUID_IDENTIFIER} in introspect_json {introspect_json}'
            )
            return None

        identifier_ = introspect_json[settings.EDUID_IDENTIFIER]
        social_account = SocialAccount.objects.filter(uid=identifier_).first()
        login_endpoint = request.path == API_LOGIN_PATH
        if social_account is None:
            if login_endpoint:
                # further logic is dealt with in /mobile/api/login
                request.mobile_api_call = True
                logger.info(f'MobileAPIAuthentication created TemporaryUser {introspect_json["email"]} for login')
                return TemporaryUser(introspect_json, bearer_token), bearer_token
            else:
                # If not heading to login-endpoint, we raise AuthenticationFailed resulting in 401
                logger.info(
                    f'MobileAPIAuthentication TemporaryUser {introspect_json["email"]} not allowed to access {request.path}'
                )
                raise AuthenticationFailed('Authentication credentials were not provided.')
        # SocialAccount always has a User
        user = social_account.user
        agree_terms_endpoint = request.path == GENERAL_TERMS_PATH
        if login_endpoint or agree_terms_endpoint:
            # further logic is dealt with in /mobile/api/login
            logger.info(f'MobileAPIAuthentication User {user.email} allowed to access {request.path}')
            request.mobile_api_call = True
            return user, bearer_token
        elif not user.general_terms_accepted() or not user.validated_name:
            # If not heading to login-endpoint or agree-terms, we raise AuthenticationFailed resulting in 401
            logger.info(
                f'MobileAPIAuthentication User {user.email} has not accepted the general terms. '
                f'Not allowed to access {request.path}'
            )
            raise AuthenticationFailed('Authentication credentials were not provided.')

        logger.info(f'MobileAPIAuthentication forwarding User {user.email} to {request.path}')
        request.mobile_api_call = True
        return user, bearer_token
