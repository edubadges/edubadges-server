import logging
from pprint import pformat
from typing import Any, Dict, Optional

import requests
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.http import Http404
from issuer.models import BadgeInstance
from mainsite.settings import EC_ISSUER_ADMIN_TOKEN, EC_ISSUER_URL
from rest_framework import permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

logger = logging.getLogger("django")


class CredentialsView(APIView):
    """
    Thin client for the ec-issuer administrative API.

    All credential templating / OpenBadges-v3 shaping and the actual
    OID4VCI protocol flow are now handled by the separate ec-issuer /
    ssi-agent services. This view only authorizes the request, resolves
    the badge instance being requested, and asks ec-issuer to create a
    credential offer for it.

    See apps/ob3/openapi.yaml for the ec-issuer API contract.

    TODO: Add GET method that the ec-issuer can call to retrieve achievement and other required data.
    """

    permission_classes = (permissions.AllowAny,)
    http_method_names = ["post"]

    def post(self, request: Request, **_kwargs: Any) -> Response:
        _ = _kwargs  # explicitly ignore kwargs

        badge_id = request.data.get("badge_id")

        badge_instance = self.__badge_instance(badge_id, request.user)
        logger.debug(f"Badge instance: {pformat(badge_instance.__dict__)}")

        offer_uri = self.__create_offer(badge_instance)
        logger.info(f"Issued credential offer for badge {badge_id}")
        logger.debug(f"Offer: {offer_uri}")

        return Response({"offer": offer_uri}, status=status.HTTP_201_CREATED)

    def __badge_instance(self, badge_id: Optional[str], user: Any) -> BadgeInstance:
        try:
            return BadgeInstance.objects.get(id=badge_id, user=user)
        except ObjectDoesNotExist:
            raise Http404

    def __create_offer(self, badge_instance: BadgeInstance) -> Optional[str]:
        """
        Ask ec-issuer to create a credential and an offer for the given
        badge instance. See "Create Credential and Offer" in
        apps/ob3/openapi.yaml.
        """
        url = f"{EC_ISSUER_URL}/api/v1/offers"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {EC_ISSUER_ADMIN_TOKEN}",
        }
        payload: Dict[str, str] = {"award_id": badge_instance.entity_id}

        logger.debug(f"Requesting offer creation: {url} {payload}")
        resp = requests.post(timeout=5, url=url, json=payload, headers=headers)
        logger.debug(f"Response: {resp.status_code} {resp.text}")

        if resp.status_code >= 400:
            msg = f"Failed to create offer:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)

        return resp.json().get("uri")
