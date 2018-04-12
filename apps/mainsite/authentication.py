from oauth2_provider.models import Application
from oauth2_provider.oauth2_backends import get_oauthlib_core
from rest_framework.authentication import BaseAuthentication


class BadgrOAuth2Authentication(BaseAuthentication):
    www_authenticate_realm = "api"

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        oauthlib_core = get_oauthlib_core()
        valid, r = oauthlib_core.verify_request(request, scopes=[])
        if valid:
            if r.client.authorization_grant_type == Application.GRANT_CLIENT_CREDENTIALS:
                return r.client.user, r.access_token
            else:
                return r.access_token.user, r.access_token
        else:
            return None
