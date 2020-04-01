from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT

from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from institution.models import Faculty, Institution
from issuer.models import Issuer, BadgeClass
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff
from staff.serializers import BadgeClassStaffSerializer, IssuerStaffSerializer, FacultyStaffSerializer, InstitutionStaffSerializer, StaffUpdateSerializer
from staff.permissions import HasObjectPermission, StaffMembershipWithinScope


class StaffListViewBase(VersionedObjectMixin, BaseEntityListView):
    http_method_names = ['post']
    permission_map = {'POST': 'may_administrate_users'}
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)

    def post(self, request, **kwargs):
        """
        create a new staff membership
        """
        object = self.get_object(request, **kwargs)  # trigger a has_object_permissions() check on the model instance
        return super(StaffListViewBase, self).post(request, **kwargs)


class StaffDetailViewBase(BaseEntityDetailView):
    """
    PUT to edit staffmembership
    DELETE to delete staffmembership
    """
    http_method_names = ['put', 'delete']
    permission_map = {'PUT': 'may_administrate_users'}
    permission_classes = (AuthenticatedWithVerifiedEmail, StaffMembershipWithinScope)
    serializer_class = StaffUpdateSerializer

    def put(self, request, **kwargs):
        object = self.get_object(request, **kwargs)  # triggers a has_object_permissions() check on the model instance
        return super(StaffDetailViewBase, self).put(request, **kwargs)

    def delete(self, request, **kwargs):
        """
        DELETE a single entity by identifier
        """
        obj = self.get_object(request, **kwargs)  # triggers a has_object_permissions() check on the model instance
        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)


class InstitutionStaffList(StaffListViewBase):
    """
    Get staff members you may administrate within an Institution context
    Post to add a new staff member within Institution context
    """
    model = Institution  # used by get_object()
    serializer_class = InstitutionStaffSerializer


class InstitutionStaffDetail(StaffDetailViewBase):
    """
    PUT to edit institution staff membership
    """

    http_method_names = ['put']  # may not delete institutionstaff membership
    model = InstitutionStaff  # used by get_object()
    serializer_class = InstitutionStaffSerializer


class FacultyStaffList(StaffListViewBase):
    """
    Get staff members you may administrate within a Faculty context
    Post to add a new staff member within Faculty context
    """
    model = Faculty
    serializer_class = FacultyStaffSerializer


class FacultyStaffDetail(StaffDetailViewBase):
    """
    PUT to edit faculty staff membership
    DELETE to delete faculty staff membership
    """
    model = FacultyStaff  # used by get_object()
    # serializer_class = FacultyStaffSerializer


class IssuerStaffList(StaffListViewBase):
    """
    Get staff members you may administrate within an Issuer context
    Post to add a new staff member within Issuer context
    """
    model = Issuer
    serializer_class = IssuerStaffSerializer


class IssuerStaffDetail(StaffDetailViewBase):
    """
    PUT to edit issuer staff membership
    DELETE to delete issuer staff membership
    """
    model = IssuerStaff  # used by get_object()
    serializer_class = IssuerStaffSerializer


class BadgeClassStaffList(StaffListViewBase):
    """
    Get staff members you may administrate within a Badgeclass context
    Post to add a new staff member within Badgeclass context
    """
    model = BadgeClass
    serializer_class = BadgeClassStaffSerializer


class BadgeClassStaffDetail(StaffDetailViewBase):
    """
    PUT to edit badgeclass staff membership
    DELETE to delete badgeclass staff membership
    """
    model = BadgeClassStaff  # used by get_object()
    serializer_class = BadgeClassStaffSerializer
