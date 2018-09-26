from oauth2_provider.oauth2_validators import OAuth2Validator, AccessToken, RefreshToken
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

    def get_existing_tokens(self, request):
        return AccessToken.objects.filter(user=request.user, application=request.client).order_by('-created')

    def _create_access_token(self, expires, request, token, *args, **kwargs):
        access_token = self.get_existing_tokens(request).first()
        if access_token:
            # reuse existing access_token and preserve original token, but bump expiration
            access_token.expires = expires
            access_token.scope = " ".join(set(access_token.scope.split()) | set(token["scope"].split()))
            access_token.save()
            token['access_token'] = access_token.token
        else:
            access_token = AccessToken.objects.create(
                user=request.user,
                application=request.client,
                scope=token["scope"],
                expires=expires,
                token=token["access_token"],
            )
        return access_token

    def save_bearer_token(self, token, request, *args, **kwargs):
        existing_access_tokens = self.get_existing_tokens(request=request)
        if len(existing_access_tokens) > 0:
            # revoke old duplicate tokens (if any) so there is only one AccessToken per user+application
            for old_token in existing_access_tokens[1:]:
                old_token.revoke()

            # pass existing refresh_token for save_bearer_token() to handle
            try:
                request.refresh_token_instance = existing_access_tokens[0].refresh_token
            except RefreshToken.DoesNotExist as e:
                pass

        super(BadgrRequestValidator, self).save_bearer_token(token, request, *args, **kwargs)





