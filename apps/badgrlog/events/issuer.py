# Created by wiggins@concentricsky.com on 8/27/15.
from django.conf import settings

from .base import BaseBadgrEvent


class IssuerCreatedEvent(BaseBadgrEvent):
    def __init__(self, serialized_issuer):
        self.issuer = serialized_issuer

    def to_representation(self):
        return {
            'creator': self.issuer.get('created_by'),
            'issuer': self.issuer.get('json'),
            'image': self.issuer.get('image'),
        }


class BadgeClassCreatedEvent(BaseBadgrEvent):
    def __init__(self, serialized_badge_class, image):
        self.badge_class = serialized_badge_class
        self.image = image

    def to_representation(self):
        return {
            'creator': self.badge_class.get('created_by'),
            'badge_class': self.badge_class.get('json'),
            'image': {
                'size': self.image.size,
                'type': self.image.content_type,
            }
        }


class BadgeClassDeletedEvent(BaseBadgrEvent):
    def __init__(self, badge_class_json, user):
        self.badge_class_json = badge_class_json
        self.user = user

    def to_representation(self):
        return {
            'deleter': settings.HTTP_ORIGIN + self.user.get_absolute_url(),
            'badge_class': self.badge_class_json
        }


