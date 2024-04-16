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
        badge_id = request.data.get('badge_id')
        badge_instance = BadgeInstance.objects.get(id=badge_id)
        if badge_instance.user != request.user:
            raise Http404

        badgeclass = badge_instance.badgeclass
        criteria = badgeclass.criteria_text
        criteria_type = "narrative"
        subject_id = str(uuid.uuid4())
        issuer = badgeclass.issuer
        request_data = {
            "subjectId": subject_id,
            "credential": {
                "issuer": {
                    "id": f"{UI_URL}/public/issuers/{issuer.entity_id}",
                    "type": [
                        "Profile"
                    ],
                    "name": issuer.name_english
                },
                "credentialSubject": {
                    "id": "",
                    "type": [
                        "AchievementSubject"
                    ],
                    "achievement": {
                        "id": f"{UI_URL}/public/assertions/{badge_instance.entity_id}",
                        "type": [
                            "Achievement"
                        ],
                        "criteria": {
                            criteria_type: criteria
                        },
                        "description": badgeclass.description,
                        "name": badgeclass.name,
                        "image": {
                            "id": badgeclass.image_url()
                        }
                    }
                }
            }
        }
        requests.post(json=request_data,
                      url=f"{OB3_API_URL}/v1/credentials",
                      headers={'Accept': 'application/json'})
        subject_id = {"subjectId": subject_id}
        response = requests.post(json=subject_id,
                                 url=f"{OB3_API_URL}/v1/offers",
                                 headers={'Accept': 'application/json'})
        response_json = response.json()

        img = qrcode.make(response_json)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return Response({"qr_code_base64": img_str}, status=status.HTTP_201_CREATED)
