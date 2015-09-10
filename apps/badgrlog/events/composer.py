# Created by wiggins@concentricsky.com on 9/10/15.
from .base import BaseBadgrEvent

class InvalidBadgeUploaded(BaseBadgrEvent):

    def __init__(self, abi, user):
        self.abi = abi
        self.user = user

    def to_representation(self):
        return {
            'user': self.user.username,
            'instance_url': self.abi.instance_url,
            'errors': self.abi.all_errors()
        }

