from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView
from institution.models import Faculty, Institution
from institution.serializers import FacultySerializer, InstitutionSerializer
from mainsite.permissions import AuthenticatedWithVerifiedEmail, CannotDeleteWithChildren
from staff.permissions import HasObjectPermission


class CheckInstitutionValidity(APIView):
    """
    Endpoint used to check if the institution is represented in the db
    POST to check, expects a shac_home string
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        data = {'valid': False}
        schac_home = request.data
        if schac_home:
            try:
                Institution.objects.get(identifier=schac_home)
                data['valid'] = True
            except Institution.DoesNotExist:
                pass
        return Response(data, status=HTTP_200_OK)


class InstitutionDetail(BaseEntityDetailView):
    """
    PUT to edit an institution
    """
    model = Institution
    v1_serializer_class = InstitutionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    http_method_names = ['put']


class FacultyDetail(BaseEntityDetailView):
    """
    PUT to edit a faculty
    DELETE to remove it
    """
    model = Faculty
    v1_serializer_class = FacultySerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission, CannotDeleteWithChildren)
    http_method_names = ['put', 'delete']


class FacultyList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a new Faculty
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    v1_serializer_class = FacultySerializer
    http_method_names = ['post']

    def post(self, request, **kwargs):
        return super(FacultyList, self).post(request, **kwargs)

