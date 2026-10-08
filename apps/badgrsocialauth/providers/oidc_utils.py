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
    config_url = f"{provider_url}/.well-known/openid-configuration"

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

    issuer = config["issuer"]
    algs = config["id_token_signing_alg_values_supported"]
    return jwt.decode(
        id_token,
        jwks,
        algorithms=algs,
        audience=client_id,
        issuer=issuer,
    )
