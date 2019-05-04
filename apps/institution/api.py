from entity.api import BaseEntityListView, BaseEntityDetailView
from institution.models import Faculty
from institution.serializers_v1 import FacultySerializerV1
from mainsite.permissions import AuthenticatedWithVerifiedEmail, MayUseManagementDashboard
from institution.permissions import ObjectWithinScope, UserHasInstitutionScope

class FacultyList(BaseEntityListView):
    """
    Faculty list
    """
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard)
    serializer_class = FacultySerializerV1
    
    def get_objects(self, request, **kwargs):
        if request.user.has_perm('badgeuser.has_institution_scope'):
            return Faculty.objects.filter(institution=self.request.user.institution)
        elif request.user.has_perm('badgeuser.has_faculty_scope'):
            return request.user.faculty.all()
        return Faculty.objects.none()

    def get(self, request, **kwargs):
        return super(FacultyList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        return super(FacultyList, self).post(request, **kwargs)
    
class FacultyDetail(BaseEntityDetailView):
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, UserHasInstitutionScope, ObjectWithinScope)
    serializer_class = FacultySerializerV1
    
    def get(self, request, **kwargs):
        return super(FacultyDetail, self).get(request, **kwargs)

    def get_object(self, request, **kwargs):
        return Faculty.objects.get(entity_id=kwargs.get('slug'))

    def put(self, request, **kwargs):
        return super(FacultyDetail, self).put(request, **kwargs)