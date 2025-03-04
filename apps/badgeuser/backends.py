from allauth.account.auth_backends import AuthenticationBackend
from badgeuser.models import BadgeUser
from django.contrib.auth.backends import ModelBackend


class CachedModelBackend(ModelBackend):
    def get_user(self, user_id):
        try:
            return BadgeUser.cached.get(pk=user_id)
        except BadgeUser.DoesNotExist:
            return None

