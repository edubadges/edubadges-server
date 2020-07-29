from django.http import Http404
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from institution.models import Institution

from .serializers import PublicInstitutionSerializer


class PublicInstitutionDetail(APIView):
    """
    POST to get public institution values like terms of service
    """
    model = Institution
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        schac_home = request.data.get('schac_home', None)
        if schac_home:
            institution = self.model.objects.get(identifier=schac_home)
            serializer = PublicInstitutionSerializer(institution)
            return Response(serializer.to_representation(institution),
                            status=HTTP_200_OK)
        raise Http404

