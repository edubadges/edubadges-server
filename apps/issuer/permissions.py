import logging

import oauth2_provider
from rest_framework import permissions

logger = logging.getLogger('Badgr.Debug')
SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


class AuditedModelOwner(permissions.BasePermission):
    """
    Request user matches .created_by
    ---
    model: BaseAuditedModel
    """
    def has_object_permission(self, request, view, obj):
        created_by_id = getattr(obj, 'created_by_id', None)
        return created_by_id and request.user.id == created_by_id


class RecipientIdentifiersMatch(permissions.BasePermission):
    """
    one of request user's verified emails matches obj.recipient_identifier
    OR
    user's edu ID matches obj.recipient_identifier
    ---
    model: BadgeInstance
    """
    def has_object_permission(self, request, view, obj):
        recipient_identifier = getattr(obj, 'recipient_identifier', None)
        verified_emails = [email.email for email in request.user.verified_emails]
        result =  recipient_identifier and recipient_identifier in request.user.all_recipient_identifiers+verified_emails
        if not result:
            logger.error('permission denied at VerifiedEmailMatchesRecipientIdentifier')
        return result
    

class BadgrOAuthTokenHasScope(permissions.BasePermission):
    def has_permission(self, request, view):
        valid_scopes = self.valid_scopes_for_view(view, method=request.method)
        token = request.auth

        if not token:
            if '*' in valid_scopes:
                return True

            # fallback scopes for authenticated users
            if request.user and request.user.is_authenticated:
                default_auth_scopes = set(['rw:profile', 'rw:issuer', 'rw:backpack'])
                if len(set(valid_scopes) & default_auth_scopes) > 0:
                    return True
            
            logger.error({'valid_scopes':valid_scopes,
                          'is_authenticated': request.user.is_authenticated,})
            return False

        # Do not apply scope if using a non-oauth tokens
        if not isinstance(token, oauth2_provider.models.AccessToken):
            return True

        # default behavior of token.is_valid(valid_scopes) requires ALL of valid_scopes on the token
        # we want to check if ANY of valid_scopes are present in the token
        matching_scopes = set(valid_scopes) & set(token.scope.split())
        return not token.is_expired() and len(matching_scopes) > 0


    @classmethod
    def valid_scopes_for_view(cls, view, method=None):
        valid_scopes = getattr(view, "valid_scopes", [])
        if isinstance(valid_scopes, dict) and method is not None:
            for m in (method, method.lower(), method.upper()):
                if m in valid_scopes:
                    return valid_scopes[m]
            return []

        return valid_scopes
