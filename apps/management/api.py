from institution.models import Faculty
from entity.api import BaseEntityListView, BaseEntityDetailView
from mainsite.permissions import AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, ObjectWithinUserScope
from django.contrib.auth.models import Group
from management.serializers import GroupSerializer, FacultySerializerStatistics


class GroupList(BaseEntityListView):
    model = Group
    http_method_names = ['get']
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, ObjectWithinUserScope)
    serializer_class = GroupSerializer


    def get_objects(self, request, **kwargs):

        return Group.objects.filter(entity_rank__rank__gte=request.user.highest_group.rank)

    def get(self, request, **kwargs):
        return super(GroupList, self).get(request, **kwargs)



class FacultyStats(BaseEntityDetailView):

    model = Faculty
    http_method_names = ['get']
    permission_classes = (AuthenticatedWithVerifiedEmail, MayUseManagementDashboard, ObjectWithinUserScope)
    serializer_class = FacultySerializerStatistics

    def get(self, request, **kwargs):
        return super(FacultyStats, self).get(request, **kwargs)
