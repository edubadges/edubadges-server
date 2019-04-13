from entity.api import BaseEntityListView, BaseEntityDetailView
from institution.models import Faculty
from institution.serializers_v1 import FacultySerializerV1
from mainsite.permissions import AuthenticatedWithVerifiedEmail, MayUseManagementDashboard
from institution.permissions import ObjectWithinScope

class FacultyList(BaseEntityListView):
    """
    Faculty list
    """
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard) 
    serializer_class = FacultySerializerV1
    
    def get_objects(self, request, **kwargs):
        return Faculty.objects.filter(institution=self.request.user.institution)
    
    def get(self, request, **kwargs):
        return super(FacultyList, self).get(request, **kwargs)
    
    
class FacultyDetail(BaseEntityDetailView):
    model = Faculty
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, ObjectWithinScope) 
    serializer_class = FacultySerializerV1
    
    def get(self, request, **kwargs):
        return super(FacultyDetail, self).get(request, **kwargs)

    def get_object(self, request, **kwargs):
        return Faculty.objects.get(id=kwargs.get('id'))

    def put(self, request, **kwargs):
        return super(FacultyDetail, self).put(request, **kwargs)