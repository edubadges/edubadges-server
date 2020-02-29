from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from institution.models import Faculty
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

    # def get_objects(self, request, **kwargs):
    #     if request.user.has_perm('badgeuser.has_institution_scope'):
    #         return Faculty.objects.filter(institution=self.request.user.institution)
    #     elif request.user.has_perm('badgeuser.has_faculty_scope'):
    #         return request.user.faculty.all()
    #     return Faculty.objects.none()
    #
    # def get(self, request, **kwargs):
    #     return super(FacultyList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        faculty = self.get_object(request, **kwargs)
        return super(FacultyIssuerList, self).post(request, **kwargs)


# class FacultyDetail(BaseEntityDetailView):
#     model = Faculty
#     permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, UserHasInstitutionScope, ObjectWithinUserScope)
#     serializer_class = FacultySerializerV1
#
#     def get(self, request, **kwargs):
#         return super(FacultyDetail, self).get(request, **kwargs)
#
#     def get_object(self, request, **kwargs):
#         return Faculty.objects.get(entity_id=kwargs.get('slug'))
#
#     def put(self, request, **kwargs):
#         return super(FacultyDetail, self).put(request, **kwargs)