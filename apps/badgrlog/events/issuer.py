# Created by wiggins@concentricsky.com on 8/27/15.

from .base import BaseBadgrEvent


class IssuerCreatedEvent(BaseBadgrEvent):
    def __init__(self, issuer):
        self.issuer = issuer

    def to_representation(self):
        return {
            'creator': self.issuer.cached_creator,
            'issuer': self.issuer.json,
            'image': self.issuer.image,
        }


class BadgeClassCreatedEvent(BaseBadgrEvent):
    def __init__(self, badge_class):
        self.badge_class = badge_class

    def to_representation(self):

        image_data = {
            'id': self.badge_class.image.url,
        }
        if hasattr(self.badge_class.image, 'size'):
            image_data['size'] = self.badge_class.image.size
        if hasattr(self.badge_class.image, 'content_type'):
            image_data['fileType'] = self.badge_class.image.content_type
        return {
            'creator': self.badge_class.cached_creator,
            'badgeClass': self.badge_class.json,
            'image': image_data
        }


class BadgeClassDeletedEvent(BaseBadgrEvent):
    def __init__(self, badge_class, user):
        self.badge_class_json = badge_class
        self.user = user

    def to_representation(self):
        return {
            'user': self.user,
            'badgeClass': self.badge_class.json,
        }


class BadgeInstanceCreatedEvent(BaseBadgrEvent):
    def __init__(self, badge_instance):
        self.badge_instance = badge_instance

    def to_representation(self):
        return {
            'creator': self.badge_instance.created_by,
            'issuer': self.badge_instance.issuer.jsonld_id,
            'recipient': self.badge_instance.recipient_identifier,
            'badgeClass': self.badge_instance.badgeclass.jsonld_id,
            'badgeInstance': self.badge_instance.json,
        }


class BadgeAssertionRevokedEvent(BaseBadgrEvent):
    def __init__(self, badge_instance, user):
        self.badge_instance = badge_instance
        self.user = user

    def to_representation(self):
        return {
            'user': self.user,
            'badgeInstance': self.badge_instance.json
        }

