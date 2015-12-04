from rest_framework.response import Response
from rest_framework.views import APIView


class BadgrLogContextView(APIView):
    permission_classes = []
    def get(self, request):

        return Response(
            {
                "@context": [
                    "https://w3id.org/openbadges/v1",
                    {
                        "sioc": "http://rdfs.org/sioc/ns#",
                        "badgeInstance": "obi:assertion",
                        "badgeClass": "obi:badge",

                        "Action": "schema:action",
                        "Image": "schema:ImageObject",

                        "timestamp": "schema:endTime",
                        "user": "schema:agent",
                        "ipAddress": "sioc:ip_address",
                        "username": "sioc:name",
                        "givenName": "schema:givenName",
                        "familyName": "schema:familyName",
                        "notification": "http://www.w3.org/ns/odrl/2/deliveryChannel",

                        "results": "obi:TBD",
                        "error": "obi:TBD",
                        "creator": "obi:TBD",
                        "size": "obi:TBD",
                        "fileType": "obi:TBD",
                        "actionType": "obi:TBD"

                    }
                ]
            }
        )
