import logging
from http import HTTPStatus
from typing import Any

import requests
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.http import Http404
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.settings import EC_ISSUER_URL
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
        _ = _kwargs

        badge_entity_id = request.data.get("badge_entity_id")

        badge_instance = self._find_badge_instance(badge_entity_id, request.user)
        if badge_instance is None:
            raise Http404("Badge instance not found")

        offer_uri = self._create_offer(request, badge_entity_id)
        logger.info(f"Issued credential offer for badge {badge_entity_id}")  # noqa: G004
        logger.debug(f"Offer: {offer_uri}")  # noqa: G004

        return Response({"offer": offer_uri}, status=status.HTTP_201_CREATED)

    def _find_badge_instance(self, entity_id: str, user) -> Any | None:
        """
        Look up a BadgeInstance by its entity_id and verify the requesting
        user is the recipient.  Returns None when the badge does not exist
        or does not belong to the user.
        """
        from issuer.models import BadgeInstance  # noqa: PLC0415

        try:
            return BadgeInstance.objects.get(entity_id=entity_id, user=user)
        except (ObjectDoesNotExist, ValueError):
            return None

    def _create_offer(self, request: Request, badge_entity_id: str) -> str | None:
        """
        Ask ec-issuer to create a credential and an offer for the given
        badge instance.
        """
        url = f"{EC_ISSUER_URL}/api/v1/offers"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {_bearer_token(request)}",
        }
        payload: dict[str, str] = {
            "award_id": badge_entity_id,
        }

        logger.debug(f"Requesting offer creation: {url} {payload['award_id']}")  # noqa: G004
        resp = requests.post(timeout=5, url=url, json=payload, headers=headers)
        logger.debug(f"Response: {resp.status_code} {resp.text}")  # noqa: G004

        if resp.status_code >= HTTPStatus.BAD_REQUEST:
            msg = f"Failed to create offer:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)

        return resp.json().get("uri")
