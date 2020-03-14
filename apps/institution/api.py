from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from institution.models import Faculty, Institution
from institution.serializers_v1 import FacultySerializerV1
from issuer.serializers_v1 import IssuerSerializerV1
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.permissions import HasObjectPermission


class FacultyIssuerList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create an Issuer within the Faculty context
    """
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = IssuerSerializerV1
    allowed_methods = ('POST',)

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
    allowed_methods = ('POST',)

    def post(self, request, **kwargs):
        self.has_object_permissions(request, request.user.institution)
        return super(InstitutionFacultyList, self).post(request, **kwargs)

