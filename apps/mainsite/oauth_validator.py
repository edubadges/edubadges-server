from django.conf import settings
from oauth2_provider.oauth2_validators import OAuth2Validator, AccessToken, RefreshToken
from oauth2_provider.scopes import get_scopes_backend
from oauthlib.oauth2 import Server


class BadgrOauthServer(Server):
    """
    used for providing a default grant type
    """
    @property
    def default_grant_type(self):
        return "password"


class BadgrRequestValidator(OAuth2Validator):

    def authenticate_client(self, request, *args, **kwargs):
        # if a request doesnt include client_id or grant_type assume defaults
        if not (request.client_id and request.grant_type and request.client_secret):
            request.grant_type = 'password'
            request.client_id = getattr(settings, 'OAUTH2_DEFAULT_CLIENT_ID', 'public')
            request.client_secret = u''
            request.scopes = ['rw:profile', 'rw:issuer', 'rw:backpack']
        return super(BadgrRequestValidator, self).authenticate_client(request, *args, **kwargs)

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        available_scopes = get_scopes_backend().get_available_scopes(application=client, request=request)

        for scope in scopes:
            if not self.is_scope_valid(scope, available_scopes):
                return False

        return True

    def is_scope_valid(self, scope, available_scopes):
        for available_scope in available_scopes:
            if available_scope.endswith(':*'):
                base_available_scope, _ = available_scope.rsplit(':*', 1)
                base_scope, _ = scope.rsplit(':', 1)

                if base_scope == base_available_scope:
                    return True
            elif scope == available_scope:
                return True

        return False

