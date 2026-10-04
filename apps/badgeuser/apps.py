from allauth.account.signals import email_confirmed, user_signed_up
from django.apps import AppConfig

from .signals import log_email_confirmed, log_user_signed_up


class BadgeUserConfig(AppConfig):
    name = "badgeuser"

    def ready(self):
        user_signed_up.connect(log_user_signed_up, dispatch_uid="user_signed_up")
        email_confirmed.connect(log_email_confirmed, dispatch_uid="email_confirmed")
