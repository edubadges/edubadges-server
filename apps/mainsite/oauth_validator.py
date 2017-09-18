from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.scopes import get_scopes_backend


class BadgrRequestValidator(OAuth2Validator):
    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        available_scopes = get_scopes_backend().get_available_scopes(application=client, request=request)

        for scope in scopes:
            if not self._validate_scope(scope, available_scopes):
                return False

        return True

    def _validate_scope(self, scope, available_scopes):
        for available_scope in available_scopes:
            if available_scope.endswith(':*'):
                base_available_scope, _ = available_scope.rsplit(':*', 1)
                base_scope, _ = scope.rsplit(':', 1)

                if base_scope == base_available_scope:
                    return True
            elif scope == available_scope:
                return True

        return False






