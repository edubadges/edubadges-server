from rest_framework.response import Response
from rest_framework.views import APIView


class BadgrLogContextView(APIView):
    def get(self, request):

        return Response(
            {
                "@context": [
                    "https://w3id.org/openbadges/v1",
                    {
                        "sioc": "http://rdfs.org/sioc/ns#",
                        "Action": "schema:action",
                        "Image": "schema:ImageObject",
                        "timestamp": "schema:endTime",
                        "user": "schema:agent",
                        "ipAddress": "sioc:ip_address",
                        "username": "sioc:name",
                        "givenName": "schema:givenName",
                        "familyName": "schema:familyName",
                        "notification": "http://www.w3.org/ns/odrl/2/deliveryChannel"
                    }
                ]
            },
            content_type='application/ld+json'
        )
