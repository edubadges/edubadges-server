from entity.api import BaseEntityListView
from institution.models import Faculty
from issuer.models import Issuer, BadgeClass
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.serializers import StaffSerializer
from staff.permissions import HasObjectPermission


class StaffListViewMixin(object):
    allowed_methods = ('POST', 'GET')
    permission_map = {'GET': 'administrate_users', 'POST': 'administrate_users'}
    serializer_class = StaffSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)

    def get_objects(self, request, **kwargs):
        """
        get users you may administrate
        """
        obj = self.get_object(request, **kwargs)
        return obj.get_administrable_staff(request.user)

    def post(self, request, **kwargs):
        """
        create a new staff membership
        """
        self.get_object(request, **kwargs)  # trigger a has_object_permissions() check
        return super(StaffList, self).post(request, **kwargs)


class FacultyStaffList(StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within a Faculty context
    Post to add a new staff member within Faculty context
    """
    model = Faculty  # used by get_object()


class IssuerStaffList(StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within an Issuer context
    Post to add a new staff member within Issuer context
    """
    model = Issuer  # used by get_object()


class BadgeClassStaffList(StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within an Issuer context
    Post to add a new staff member within Issuer context
    """
    model = BadgeClass  # used by get_object()


class StaffList(StaffListViewMixin, BaseEntityListView):
    """
    Get all staff members you may administrate
    """
    allowed_methods = ('GET',)
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    def get_objects(self, request, **kwargs):
        """
        Get users you may administrate
        """
        return request.user.get_administrable_staff()
