import base64
import uuid
from io import BytesIO

import qrcode
import requests
from django.http import Http404
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.models import BadgeInstance
from mainsite.settings import OB3_API_URL, UI_URL

class CredentialsView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        offer_id = str(uuid.uuid4())
        badge_id = request.data.get('badge_id')

        badge_instance = self.__badge_instance(badge_id, request.user)
        request_data = self.__request_data(offer_id, badge_instance)

        self.__issue_badge(badge_instance)
        credential_offer = self.__get_offer(offer_id)
        img_str = self.__qr_code(credential_offer)
        return Response({"qr_code_base64": img_str}, status=status.HTTP_201_CREATED)

    def __badge_instance(self, badge_id, user):
        try:
            return BadgeInstance.objects.get(id=badge_id, user=user)
        except BadgeInstance.DoesNotExist:
            raise Http404

    def __issue_badge(self, badge_instance):
        requests.post(json=request_data,
                      url=f"{OB3_API_URL}/v0/credentials",
                      headers={'Accept': 'application/json'})

    def __get_offer(self, offer_id):
        offer_id = {"offerId": offer_id}
        response = requests.post(json=offer_id,
                                 url=f"{OB3_API_URL}/v0/offers",
                                 headers={'Accept': 'application/json'})

        return response.text


    def __request_data(self, offer_id, badge_instance):
        badgeclass = badge_instance.badgeclass
        criteria = badgeclass.criteria_text
        issuer = badgeclass.issuer
        return {
            "offerId": offer_id,
            "credentialConfigurationId": "openbadge_credential",
            "credential": {
                "issuer": {
                    "id": f"{UI_URL}/public/issuers/{issuer.entity_id}",
                    "type": [
                        "Profile"
                    ],
                    "name": issuer.name_english
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
                            "narrative": criteria
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
