import random
import string
import base64
from hashlib import md5

from allauth.account.adapter import get_adapter
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.template import Context

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


def generate_badgr_username(email):
    # md5 hash the email and then encode as base64 to take up only 25 characters
    salted_email = (email + ''.join(random.choice(string.ascii_lowercase) for i in range(64))).encode('utf-8')
    hashed = str(base64.b64encode(md5(salted_email).hexdigest().encode('utf-8')), 'utf-8')
    return "badgr{}".format(hashed[:25])