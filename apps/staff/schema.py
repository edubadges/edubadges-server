import graphene
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

class PermissionType(graphene.ObjectType):
    may_create = graphene.Boolean()
    may_read = graphene.Boolean()
    may_update = graphene.Boolean()
    may_delete = graphene.Boolean()
    may_award = graphene.Boolean()
    may_sign = graphene.Boolean()
    may_administrate_users = graphene.Boolean()

