import logging
from typing import Any, Dict, Optional

import requests
from django.core.exceptions import BadRequest
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.settings import EC_ISSUER_ADMIN_TOKEN, EC_ISSUER_URL
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("django")


def _bearer_token(request: Request) -> str:
    """
    Extract the raw bearer token from the Authorization header of an
    already-authenticated request, so it can be forwarded to ec-issuer.
    """
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.lower().startswith("bearer "):
        # Should not happen once permission_classes requires authentication,
        # but we can't forward a token we don't have.
        raise BadRequest("Missing bearer token, cannot forward it to ec-issuer")
    return auth_header.split(" ", 1)[1]


class CredentialsView(APIView):
    """
    Thin client for the ec-issuer administrative API, and the endpoint
    ec-issuer calls back into to authenticate the user and fetch award data.

    All credential templating / OpenBadges-v3 shaping and the actual
    OID4VCI protocol flow are handled by the separate ec-issuer / ssi-agent
    services:
    - POST: resolves the badge instance being requested and asks ec-issuer
      to create a credential offer for it, forwarding the caller's own
      access token.

    """

    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ["post"]

    def post(self, request: Request, **_kwargs: Any) -> Response:
        _ = _kwargs  # explicitly ignore kwargs

        badge_entity_id = request.data.get("badge_entity_id")

        offer_uri = self.__create_offer(request, badge_entity_id)
        logger.info(f"Issued credential offer for badge {badge_entity_id}")
        logger.debug(f"Offer: {offer_uri}")

        return Response({"offer": offer_uri}, status=status.HTTP_201_CREATED)

    def __create_offer(self, request: Request, badge_entity_id: str) -> Optional[str]:
        """
        Ask ec-issuer to create a credential and an offer for the given
        badge instance. See "Create Credential and Offer" in
        apps/ob3/openapi.yaml.

        The requesting user's own access token is forwarded so ec-issuer can
        later present it back to us (this view's GET method) to authenticate
        the user and fetch the award data needed to serialize an OpenBadges
        v3 credential.
        """
        url = f"{EC_ISSUER_URL}/api/v1/offers"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {EC_ISSUER_ADMIN_TOKEN}",
        }
        payload: Dict[str, str] = {
            "award_id": badge_entity_id,
            "access_token": _bearer_token(request),
        }

        logger.debug(f"Requesting offer creation: {url} {payload['award_id']}")
        resp = requests.post(timeout=5, url=url, json=payload, headers=headers)
        logger.debug(f"Response: {resp.status_code} {resp.text}")

        if resp.status_code >= 400:
            msg = f"Failed to create offer:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)

        return resp.json().get("uri")
