# Created by wiggins@concentricsky.com on 8/27/15.

from .base import BaseBadgrEvent


class IssuerCreatedEvent(BaseBadgrEvent):
    def __init__(self, issuer):
        self.issuer = issuer

    def to_representation(self):
        return {
            'issuer': self.issuer.get('json'),
            'image': self.issuer.get('image'),
            'creator': self.issuer.get('created_by'),
        }
