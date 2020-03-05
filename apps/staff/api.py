from entity.api import BaseEntityListView, VersionedObjectMixin
from institution.models import Faculty, Institution
from issuer.models import Issuer, BadgeClass
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.serializers import BadgeClassStaffSerializer, IssuerStaffSerializer, FacultyStaffSerializer, InstitutionStaffSerializer
from staff.permissions import HasObjectPermission


class StaffListViewMixin(object):
    allowed_methods = ('POST',)
    permission_map = {'POST': 'may_administrate_users'}

    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)

    def post(self, request, **kwargs):
        """
        create a new staff membership
        """
        object = self.get_object(request, **kwargs)  # trigger a has_object_permissions() check on the model instance
        return super(StaffListViewMixin, self).post(request, **kwargs)


class InstitutionStaffList(VersionedObjectMixin, StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within a Faculty context
    Post to add a new staff member within Faculty context
    """
    model = Institution  # used by get_object()
    serializer_class = InstitutionStaffSerializer


class FacultyStaffList(VersionedObjectMixin, StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within a Faculty context
    Post to add a new staff member within Faculty context
    """
    model = Faculty
    serializer_class = FacultyStaffSerializer


class IssuerStaffList(VersionedObjectMixin, StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within an Issuer context
    Post to add a new staff member within Issuer context
    """
    model = Issuer
    serializer_class = IssuerStaffSerializer


class BadgeClassStaffList(VersionedObjectMixin, StaffListViewMixin, BaseEntityListView):
    """
    Get staff members you may administrate within an Issuer context
    Post to add a new staff member within Issuer context
    """
    model = BadgeClass
    serializer_class = BadgeClassStaffSerializer
