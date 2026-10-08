"""Shared OIDC helpers for eduID and SURFconext authentication."""

import logging

from urllib.parse import urlparse

import requests

from jose import jwt
from jose.exceptions import JWTError

logger = logging.getLogger("Badgr.Debug")


def verify_id_token(id_token: str, provider_url: str, client_id: str) -> dict:
    """Verify an OIDC id_token JWT and return its claims.

    Fetches the JWKS dynamically via the provider's
    ``/.well-known/openid-configuration`` discovery document, then decodes
    using RS256 with audience and issuer validation.
    """
    allowed_hosts = {"connect.surfconext.nl", "connect.test.surfconext.nl", "connect.eduid.nl", "connect.test.eduid.nl"}
    parsed = urlparse(provider_url)
    if parsed.hostname not in allowed_hosts:
        raise JWTError(f"Disallowed provider URL: {provider_url}")

    # The well-known endpoint sits at the host root (not under /oidc).
    base = f"{parsed.scheme}://{parsed.hostname}"
    config_url = f"{base}/.well-known/openid-configuration"

    try:
        resp = requests.get(config_url, timeout=10)
        resp.raise_for_status()
        config = resp.json()
    except Exception:
        logger.exception("Failed to fetch OIDC config from %s", config_url)
        raise JWTError("Could not retrieve signing keys from provider") from None

    try:
        resp = requests.get(config["jwks_uri"], timeout=10)
        resp.raise_for_status()
        jwks = resp.json()
    except Exception:
        logger.exception("Failed to fetch JWKS from %s", config["jwks_uri"])
        raise JWTError("Could not retrieve signing keys from provider") from None

    issuer = config.get("issuer", provider_url)
    return jwt.decode(
        id_token,
        jwks,
        algorithms=["RS256"],
        audience=client_id,
        issuer=issuer,
    )
