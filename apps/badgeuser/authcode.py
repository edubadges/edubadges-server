# encoding: utf-8


import datetime
import json

import dateutil
import cryptography.fernet
from django.conf import settings
from django.utils import timezone
from oauth2_provider.models import AccessToken

from badgeuser.models import BadgrAccessToken


def authcode_for_accesstoken(accesstoken, expires_seconds=None, secret_key=None):
    payload = accesstoken.pk
    return encrypt_authcode(payload, expires_seconds=expires_seconds, secret_key=secret_key)


def accesstoken_for_authcode(authcode, secret_key=None):
    accesstoken_pk = decrypt_authcode(authcode, secret_key=secret_key)
    try:
        return BadgrAccessToken.objects.get(pk=accesstoken_pk)
    except AccessToken.DoesNotExist:
        return None


def encrypt_authcode(payload, expires_seconds=None, secret_key=None):
    if expires_seconds is None:
        expires_seconds = getattr(settings, 'AUTHCODE_EXPIRES_SECONDS', 10)

    if secret_key is None:
        secret_key = getattr(settings, 'AUTHCODE_SECRET_KEY', None)
        if secret_key is None:
            raise ValueError("must specify a secret key")

    crypto = cryptography.fernet.Fernet(secret_key)
    digest = crypto.encrypt(_marshall(payload, expires_seconds))
    return digest


def decrypt_authcode(cipher, secret_key=None):
    if secret_key is None:
        secret_key = getattr(settings, 'AUTHCODE_SECRET_KEY', None)
        if secret_key is None:
            raise ValueError("must specify a secret key")

    crypto = cryptography.fernet.Fernet(secret_key)

    try:
        decrypted = crypto.decrypt(cipher.encode('utf-8'))
    except (cryptography.fernet.InvalidToken, UnicodeEncodeError, UnicodeDecodeError) as e:
        return None
    message = _unmarshall(decrypted)
    if message and 'expires' in message:
        expires = dateutil.parser.parse(message.get('expires'))
        if expires > timezone.now():
            payload = message.get('payload')
            return payload


# helper functions for {encrypt,decrypt}_authcode

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
