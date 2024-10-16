import base64
import uuid
from io import BytesIO

import json
import qrcode
import requests
import logging
from django.http import Http404
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.models import BadgeInstance
from mainsite.settings import OB3_AGENT_URL_SPHEREON, OB3_AGENT_AUTHZ_TOKEN_SPHEREON, OB3_AGENT_URL_UNIME, UI_URL

logger = logging.getLogger(__name__)

class CredentialsView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        offer_id = str(uuid.uuid4())
        badge_id = request.data.get('badge_id')
        variant = request.data.get('variant')

        badge_instance = self.__badge_instance(badge_id, request.user)
        credential = self.__credential(offer_id, badge_instance)

        if variant == 'sphereon':
            credential.update({"credentialConfigurationId": "OpenBadgeCredential"})
            logger.debug(f"Requesting badge w sphereon for {badge_instance.entity_id}")
            open_id_credential_offer = self.__issue_sphereon_badge(credential)
            # We get back a json object that wraps an openid-credential-offer:// uri
            # Inside this, is a a parameter credential_offer_uri that contains the actual offer uri
            # Which we can fetch to get the offer
            offer = json.loads(open_id_credential_offer).get('uri')

        elif variant == 'unime':
           credential.update({"credentialConfigurationId": "openbadge_credential"})

           logger.debug(f"Requesting badge w unime for {badge_instance.entity_id}")
           self.__issue_unime_badge(credential)
           offer = self.__get_offer(offer_id)
        else:
            raise Http404 # Should best be a 400 error, but that seems hard in Django?

        img_str = self.__qr_code(offer)
        return Response({"qr_code_base64": img_str}, status=status.HTTP_201_CREATED)

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
            "CredentialDataSupplierInput": credential
        }
        resp = requests.post(json=offer_request_body,
                      url=f"{OB3_AGENT_URL_SPHEREON}/edubadges/api/create-offer",
                      headers={'Accept': 'application/json',
                               "Authorization": f"Bearer {OB3_AGENT_AUTHZ_TOKEN_SPHEREON}"})
        logger.info(f"Sphereon response: {resp.text}")
        if resp.status_code != 200:
            msg = f"Failed to issue badge:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)

        return resp.text

    def __issue_unime_badge(self, credential):
        resp = requests.post(json=credential,
                      url=f"{OB3_AGENT_URL_UNIME}/v0/credentials",
                      headers={'Accept': 'application/json'})
        logger.debug(f"Unime response: {resp.text}")

        if resp.status_code != 200:
            msg = f"Failed to issue badge:\n\tcode: {resp.status_code}\n\tcontent:\n {resp.text}"
            raise BadRequest(msg)


    def __get_offer(self, offer_id):
        offer_id = {"offerId": offer_id}
        response = requests.post(json=offer_id,
                                 url=f"{OB3_AGENT_URL_UNIME}/v0/offers",
                                 headers={'Accept': 'application/json'})

        return response.text

    def __credential(self, offer_id, badge_instance):
        badgeclass = badge_instance.badgeclass

        return {
            "offerId": offer_id,
            "credentialConfigurationId": None,
            "credential": {
                "issuer": {
                    "id": f"{UI_URL}/public/issuers/{badgeclass.issuer.entity_id}",
                    "type": [
                        "Profile"
                    ],
                    "name": badgeclass.issuer.name_english
                },
                "credentialSubject": {
                    "type": [
                        "AchievementSubject"
                    ],
                    "achievement": {
                        "id": f"{UI_URL}/public/assertions/{badge_instance.entity_id}",
                        "type": [
                            "Achievement"
                        ],
                        "criteria": {
                            "narrative": badgeclass.criteria_text
                        },
                        "description": badgeclass.description,
                        "name": badgeclass.name,
                        "image": {
                            "type":"Image",
                            "id": badgeclass.image_url()
                        }
                    }
                }
            }
        }

    def __qr_code(self, credential_offer):
        img = qrcode.make(credential_offer)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
