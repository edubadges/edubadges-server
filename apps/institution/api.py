from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView
from institution.models import Faculty, Institution
from institution.serializers_v1 import FacultySerializerV1, InstitutionSerializer
from issuer.serializers_v1 import IssuerSerializerV1
from mainsite.permissions import AuthenticatedWithVerifiedEmail, CannotDeleteWithChildren
from staff.permissions import HasObjectPermission
from issuer.permissions import IssuedAssertionsBlock


class InstitutionDetail(BaseEntityDetailView):
    model = Institution
    v1_serializer_class = InstitutionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission, IssuedAssertionsBlock)
    http_method_names = ['put']


class FacultyDetail(BaseEntityDetailView):
    """
    PUT to edit a faculty
    DELETE to remove it
    """
    model = Faculty
    v1_serializer_class = FacultySerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission, IssuedAssertionsBlock, CannotDeleteWithChildren)
    http_method_names = ['put', 'delete']


class FacultyIssuerList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create an Issuer within the Faculty context
    """
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = IssuerSerializerV1
    http_method_names = ['post']

    def post(self, request, **kwargs):
        faculty = self.get_object(request, **kwargs)
        return super(FacultyIssuerList, self).post(request, **kwargs)


class InstitutionFacultyList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a Faculty within the Institution context
    """
    # no need to declare model here
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = FacultySerializerV1
    http_method_names = ['post']

    def post(self, request, **kwargs):
        self.has_object_permissions(request, request.user.institution)
        return super(InstitutionFacultyList, self).post(request, **kwargs)

