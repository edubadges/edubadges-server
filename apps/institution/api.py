from entity.api import BaseEntityListView
from institution.models import Faculty
from institution.serializers_v1 import FacultySerializerV1
from mainsite.permissions import AuthenticatedWithVerifiedEmail, MayUseManagementDashboard


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