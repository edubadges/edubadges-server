from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView, BaseArchiveView
from institution.models import Faculty, Institution, BadgeClassTag
from institution.serializers import FacultySerializer, InstitutionSerializer, InstitutionAuditLogSerializer, FacultyAuditLogSerializer
from mainsite.auditlog_api import BaseAuditLogView
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


class FacultyArchiveView(BaseEntityDetailView):
    model = Faculty
    v1_serializer_class = FacultySerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    http_method_names = ['put']

    def put(self, request, **kwargs):
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=HTTP_404_NOT_FOUND)
        obj.archived = False if request.data['archive'] else True
        obj.save()
        return Response(status=HTTP_204_NO_CONTENT, data={})


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


class InstitutionsTagUsage(APIView):
    """
    Endpoint used to check if a tag is being used by non-archived badge classes within the users institution
    POST to check, expects a single dict with the tag name to check
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']

    def post(self, request, **kwargs):
        tag_name = request.data.get("name")

        from issuer.models import BadgeClass

        badge_classes = BadgeClass.objects \
            .filter(tags__name=tag_name) \
            .filter(archived=False) \
            .filter(issuer__faculty__institution=request.user.institution) \
            .all()
        data = [{"name": bc.name} for bc in badge_classes]
        return Response(data, status=HTTP_200_OK)


class InstitutionAuditLog(BaseAuditLogView):
    model = Institution
    serializer_class = InstitutionAuditLogSerializer


class FacultyAuditLog(BaseAuditLogView):
    model = Faculty
    serializer_class = FacultyAuditLogSerializer
