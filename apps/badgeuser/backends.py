# Created by wiggins@concentricsky.com on 9/3/15.
from allauth.account.auth_backends import AuthenticationBackend
from badgeuser.models import BadgeUser
from django.contrib.auth.backends import ModelBackend


class CachedModelBackend(ModelBackend):
    def get_user(self, user_id):
        try:
            return BadgeUser.cached.get(pk=user_id)
        except BadgeUser.DoesNotExist:
            return None


class CachedAuthenticationBackend(CachedModelBackend, AuthenticationBackend):
    pass

