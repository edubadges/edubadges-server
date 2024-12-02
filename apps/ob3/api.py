import uuid

import requests
import logging
from django.http import Http404
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from pprint import pformat

from issuer.models import BadgeInstance
from mainsite.settings import OB3_AGENT_URL_SPHEREON, OB3_AGENT_AUTHZ_TOKEN_SPHEREON, OB3_AGENT_URL_UNIME
from .serializers import OfferRequestSerializer
from .models import OfferRequest

logger = logging.getLogger('django')

class CredentialsView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **_kwargs):
        _ = _kwargs # explicitly ignore kwargs

        offer_id = str(uuid.uuid4())
        badge_id = request.data.get('badge_id')
        variant = request.data.get('variant')

        badge_instance = self.__badge_instance(badge_id, request.user)
        logger.debug(f"Badge instance: {pformat(badge_instance.__dict__)}")
        credential_configuration_id = {
            'sphereon': "OpenBadgeCredential",
            'unime': "openbadge_credential"
        }.get(variant) 
        credential = OfferRequest(offer_id, credential_configuration_id, badge_instance)
        serializer = OfferRequestSerializer(credential)

        if variant == 'sphereon':
            offer = self.__issue_sphereon_badge(serializer.data)
            logger.debug(f"Sphereon offer: {offer}")
        elif variant == 'unime':
            self.__issue_unime_badge(serializer.data)
            offer = self.__get_unime_offer(offer_id)
            logger.debug(f"Unime offer: {offer}")

        offer = self.__issue_sphereon_badge(serializer.data)

        logger.info(f"Issued credential for badge {badge_id} with offer_id {offer_id}")
        logger.debug(f"Credential: {pformat(serializer.data)}")

        return Response({"offer": offer}, status=status.HTTP_201_CREATED)

    def __badge_instance(self, badge_id, user):
        try:
            return BadgeInstance.objects.get(id=badge_id, user=user)
        except ObjectDoesNotExist:
            raise Http404

    def __issue_sphereon_badge(self, credential):
        offer_request_body = {
            "credentials": ["OpenBadgeCredential"],
            "grants": {
                "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                    "pre-authorized_code": "This-is-sent-via-SMS",
                    "user_pin_required": False
                }
            },
            "credentialDataSupplierInput": credential
        }
        resp = requests.post(
                timeout=5,
                url=f"{OB3_AGENT_URL_SPHEREON}/edubadges/api/create-offer",
                json=offer_request_body,
                headers={'Accept': 'application/json',
                         "Authorization": f"Bearer {OB3_AGENT_AUTHZ_TOKEN_SPHEREON}"}
        )

        if resp.status_code >= 400:
            msg = f"Failed to issue badge:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)


        # We get back a json object that wraps an openid-credential-offer:// uri
        # Inside this, is a a parameter credential_offer_uri that contains the actual offer uri
        # Which we can fetch to get the offer
        json_resp = resp.json()
        return json_resp.get('uri')

    def __issue_unime_badge(self, credential):
        resp = requests.post(
                timeout=5,
                json=credential,
                url=f"{OB3_AGENT_URL_UNIME}/v0/credentials",
                headers={'Accept': 'application/json'}
        )

        if resp.status_code >= 400:
            msg = f"Failed to issue badge:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)

    def __get_unime_offer(self, offer_id):
        response = requests.post(
                timeout=5,
                url=f"{OB3_AGENT_URL_UNIME}/v0/offers",
                json= { "offerId": offer_id },
                headers={'Accept': 'application/json'}
        )

        return response.text
