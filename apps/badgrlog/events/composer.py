# Created by wiggins@concentricsky.com on 9/10/15.
from .base import BaseBadgrEvent


class InvalidBadgeUploaded(BaseBadgrEvent):

    def __init__(self, badge_check, user):
        self.badge_check = badge_check
        self.user = user

    def to_representation(self):
        return {
            'user': self.user.username,
            'instance': self.badge_checker.to_representation(),
            'results': self.badge_check.results
        }

