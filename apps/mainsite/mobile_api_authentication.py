import logging
import urllib.error
import urllib.parse
import urllib.request

from http import HTTPStatus

import requests

from allauth.socialaccount.models import SocialAccount
from django.conf import settings
from mainsite.exceptions import TermsNotAcceptedException
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

GENERAL_TERMS_PATH = "/mobile/api/accept-general-terms"
PROFILE_PATH = "/mobile/api/profile"
API_LOGIN_PATH = "/mobile/api/login"


class TemporaryUser:
    def __init__(self, user_payload, bearer_token):
        # Not saved to DB
        self.user_payload = user_payload
        self.bearer_token = bearer_token


class MobileAPIAuthentication(BaseAuthentication):
    def authenticate(self, request):  # noqa: C901, PLR0911, PLR0912, PLR0915
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        logger = logging.getLogger("Badgr.Debug")
        x_requested_with = request.headers.get("x-requested-with")
        if not x_requested_with or x_requested_with.lower() != "mobile":
            logger.info("Skipping MobileAPIAuthentication as HTTP_X_REQUESTED_WITH is NOT mobile")
            return None

        logger.info(f"MobileAPIAuthentication {request.META}")  # noqa: G004
        authorization = request.environ.get("HTTP_AUTHORIZATION")
        if not authorization:
            logger.info("MobileAPIAuthentication: raise AuthenticationFailed as no authorization header")
            raise AuthenticationFailed("Authentication credentials were not provided.")

        bearer_token = authorization[len("bearer ") :]
        if not bearer_token:
            logger.info("MobileAPIAuthentication: raise AuthenticationFailed as no bearer_token in authorization")
            raise AuthenticationFailed("Authentication credentials were not provided.")

        bearer_token = authorization[len("bearer ") :]
        if not bearer_token:
            logger.info("MobileAPIAuthentication: return None as no bearer_token in authorization")
            return None

        headers = {"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"}
        url = f"{settings.EDUID_PROVIDER_URL}/introspect"
        auth = (settings.OIDC_RS_ENTITY_ID, settings.OIDC_RS_SECRET)
        response = requests.post(
            url, data=urllib.parse.urlencode({"token": bearer_token}), auth=auth, headers=headers, timeout=60
        )
        if response.status_code != HTTPStatus.OK:
            logger.info(f"MobileAPIAuthentication bad response from oidcng: {response.status_code} {response.json()}")  # noqa: G004
            raise AuthenticationFailed("Invalid authentication credentials.")

        introspect_json = response.json()
        logger.info(f"MobileAPIAuthentication introspect {introspect_json}")  # noqa: G004

        if not introspect_json["active"]:
            logger.info(f"MobileAPIAuthentication inactive introspect_json {introspect_json}")  # noqa: G004
            raise AuthenticationFailed("Invalid authentication credentials.")
        if settings.EDUID_IDENTIFIER not in introspect_json:
            logger.info(
                f"MobileAPIAuthentication raise AuthenticationFailed as no {settings.EDUID_IDENTIFIER} in introspect_json {introspect_json}"  # noqa: E501, G004
            )
            raise AuthenticationFailed("Invalid authentication credentials.")

        introspect_json = response.json()
        logger.info(f"MobileAPIAuthentication introspect {introspect_json}")  # noqa: G004

        if not introspect_json["active"]:
            logger.info(f"MobileAPIAuthentication inactive introspect_json {introspect_json}")  # noqa: G004
            return None
        if settings.EDUID_IDENTIFIER not in introspect_json:
            logger.info(
                f"MobileAPIAuthentication return None as no {settings.EDUID_IDENTIFIER} in introspect_json {introspect_json}"  # noqa: E501, G004
            )
            return None

        identifier_ = introspect_json[settings.EDUID_IDENTIFIER]
        social_account = SocialAccount.objects.filter(uid=identifier_).first()
        login_endpoint = request.path == API_LOGIN_PATH
        if social_account is None:
            if login_endpoint:
                # further logic is dealt with in /mobile/api/login
                request.mobile_api_call = True
                logger.info(f"MobileAPIAuthentication created TemporaryUser {introspect_json['email']} for login")  # noqa: G004
                return TemporaryUser(introspect_json, bearer_token), bearer_token
            # If not heading to login-endpoint, we raise AuthenticationFailed resulting in 401
            logger.info(
                f"MobileAPIAuthentication TemporaryUser {introspect_json['email']} not allowed to access {request.path}"  # noqa: G004
            )
            raise AuthenticationFailed("Authentication credentials were not provided.")
        # SocialAccount always has a User
        user = social_account.user
        agree_terms_endpoint = request.path == GENERAL_TERMS_PATH
        profile_endpoint = request.path == PROFILE_PATH
        if login_endpoint or agree_terms_endpoint or profile_endpoint:
            # further logic is dealt with in /mobile/api/login
            logger.info(f"MobileAPIAuthentication User {user.email} allowed to access {request.path}")  # noqa: G004
            request.mobile_api_call = True
            return user, bearer_token
        if not user.general_terms_accepted():
            # If not heading to login-endpoint or agree-terms, we raise TermsNotAccepted resulting in 403
            # The mobile app depends on the detail of the error message, so it should not be changed without notifying.
            logger.info(
                f"MobileAPIAuthentication User {user.email} has not accepted the general terms. "  # noqa: G004
                f"Not allowed to access {request.path}"
            )
            raise TermsNotAcceptedException

        logger.info(f"MobileAPIAuthentication forwarding User {user.email} to {request.path}")  # noqa: G004
        request.mobile_api_call = True
        return user, bearer_token
