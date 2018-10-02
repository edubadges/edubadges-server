import datetime
import json

import dateutil
from allauth.account.adapter import get_adapter
from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template import Context
from django.utils import timezone

from mainsite.models import BadgrApp


def notify_on_password_change(user, request=None):
    """
    Sends an email notification to a user's primary email address to notify them a password change was successful.
    """
    badgr_app = BadgrApp.objects.get_current(request=request)
    base_context = {
        'user': user,
        'site': get_current_site(request),
        'help_email': getattr(settings, 'HELP_EMAIL', 'help@badgr.io'),
        'STATIC_URL': getattr(settings, 'STATIC_URL'),
        'HTTP_ORIGIN': getattr(settings, 'HTTP_ORIGIN'),
        'badgr_app': badgr_app,
    }

    email_context = Context(base_context)
    get_adapter().send_mail('account/email/password_reset_confirmation', user.primary_email, base_context)


def generate_auth_code(payload, expires_seconds=600, secret_key=None):
    if secret_key is None:
        secret_key = getattr(settings, 'AUTHCODE_SECRET_KEY', None)
        if secret_key is None:
            raise ValueError("must specify a secret key")
    crypto = Fernet(secret_key)
    digest = crypto.encrypt(_marshall(payload, expires_seconds))
    return digest


def decrypt_auth_code(cipher, secret_key=None):
    if secret_key is None:
        secret_key = getattr(settings, 'AUTHCODE_SECRET_KEY', None)
        if secret_key is None:
            raise ValueError("must specify a secret key")

    crypto = Fernet(secret_key)
    message = _unmarshall(crypto.decrypt(cipher))
    if message and 'expires' in message:
        expires = dateutil.parser.parse(message.get('expires'))
        if expires > timezone.now():
            payload = message.get('payload')
            return payload


# helper functions for generate/decrypt_auth_code

def _marshall(payload, expires_seconds):
    expires_at = timezone.now() + datetime.timedelta(seconds=expires_seconds)
    return json.dumps(dict(
        expires=expires_at.isoformat(),
        payload=payload
    ))


def _unmarshall(digest):
    try:
        return json.loads(digest)
    except ValueError:
        pass
