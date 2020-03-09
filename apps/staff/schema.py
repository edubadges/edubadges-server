from graphene_django.types import DjangoObjectType
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class StaffTypeMeta(object):

    class Meta:
        fields = ('user', 'may_create', 'may_read', 'may_update', 'may_delete', 'may_award', 'may_sign', 'may_administrate_users')


class InstitutionStaffType(DjangoObjectType):

    class Meta(StaffTypeMeta):
        model = InstitutionStaff


class FacultyStaffType(DjangoObjectType):

    class Meta(StaffTypeMeta):
        model = FacultyStaff


class IssuerStaffType(DjangoObjectType):

    class Meta(StaffTypeMeta):
        model = IssuerStaff


class BadgeClassStaffType(DjangoObjectType):

    class Meta(StaffTypeMeta):
        model = BadgeClassStaff


