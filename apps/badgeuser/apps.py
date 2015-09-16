from django.apps import AppConfig

from allauth.account.signals import user_signed_up, email_confirmed

from .signals import log_user_signed_up, log_email_confirmed


class BadgeUserConfig(AppConfig):
    name='badgeuser'

    def ready(self):
        user_signed_up.connect(log_user_signed_up,
                               dispatch_uid="user_signed_up")
        email_confirmed.connect(log_email_confirmed,
                                dispatch_uid="email_confirmed")
