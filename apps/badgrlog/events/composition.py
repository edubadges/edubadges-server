# Created by wiggins@concentricsky.com on 9/10/15.
from .base import BaseBadgrEvent


class BadgeUploaded(BaseBadgrEvent):

    def __init__(self, instance_json, badge_check, user):
        self.instance_json = instance_json
        self.badge_check = badge_check
        self.user = user

    def to_representation(self):
        return {
            'user': self.user.username,
            'instance': self.instance_json,
            'results': self.badge_check.results
        }


class InvalidBadgeUploaded(BaseBadgrEvent):

    def __init__(self, components, error, user):
        self.components = components
        self.error = error
        self.user = user

    def to_representation(self):
        return {
            'user': self.user.username,
            'instance': self.components.badge_instance,
            'badge': self.components.badge_class,
            'issuer': self.components.issuer,
            'error': self.error
        }
