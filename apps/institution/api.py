from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView, BaseArchiveView
from institution.models import Faculty, Institution
from institution.serializers import FacultySerializer, InstitutionSerializer
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.permissions import HasObjectPermission


class PublicCheckInstitutionsValidity(APIView):
    """
    Endpoint used to check if the institution is represented in the db
    POST to check, expects a schac_home string
    """
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        data = []
        schac_homes = request.data
        if schac_homes:
            for schac_home in schac_homes:
                valid = {'schac_home': schac_home, 'valid': False}
                try:
                    Institution.objects.get(identifier=schac_home)
                    valid['valid'] = True
                except Institution.DoesNotExist:
                    pass
                data.append(valid)
        return Response(data, status=HTTP_200_OK)


class InstitutionDetail(BaseEntityDetailView):
    """
    PUT to edit an institution
    """
    model = Institution
    v1_serializer_class = InstitutionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    http_method_names = ['put']


class FacultyDeleteView(BaseArchiveView):
    model = Faculty
    v1_serializer_class = FacultySerializer


class FacultyDetail(BaseEntityDetailView):
    """
    PUT to edit a faculty
    DELETE to remove it
    """
    model = Faculty
    v1_serializer_class = FacultySerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    http_method_names = ['put']


class FacultyList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a new Faculty
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    v1_serializer_class = FacultySerializer
    http_method_names = ['post']

    def post(self, request, **kwargs):
        return super(FacultyList, self).post(request, **kwargs)
