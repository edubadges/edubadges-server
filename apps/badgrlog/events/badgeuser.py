from .base import BaseBadgrEvent


class UserSignedUp(BaseBadgrEvent):

    def __init__(self, request, user, **kwargs):
        self.request = request
        self.user = user

    def to_representation(self):
        return {
            'username': self.user.username,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'email': self.user.email,
        }


class EmailConfirmed(BaseBadgrEvent):

    def __init__(self, request, email_address, **kwargs):
        self.request = request
        self.email_address = email_address

    def to_representation(self):
        return {
            'email': self.email_address.email,
        }
