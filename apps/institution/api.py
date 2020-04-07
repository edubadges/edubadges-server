from entity.api import BaseEntityListView, VersionedObjectMixin, BaseEntityDetailView
from institution.models import Faculty, Institution
from institution.serializers import FacultySerializer, InstitutionSerializer
from mainsite.permissions import AuthenticatedWithVerifiedEmail, CannotDeleteWithChildren
from staff.permissions import HasObjectPermission
from issuer.permissions import IssuedAssertionsBlock


class InstitutionDetail(BaseEntityDetailView):
    """
    PUT to edit an institution
    """
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
    v1_serializer_class = FacultySerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission, IssuedAssertionsBlock, CannotDeleteWithChildren)
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

