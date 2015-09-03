# Created by wiggins@concentricsky.com on 9/3/15.
from django.contrib.auth.backends import ModelBackend
from badgeuser.models import BadgeUser


class CachedModelBackend(ModelBackend):
    def get_user(self, user_id):
        try:
            return BadgeUser.cached.get(pk=user_id)
        except BadgeUser.DoesNotExist:
            return None
