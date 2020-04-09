import graphene
from graphene_django.types import DjangoObjectType
from .models import Institution, Faculty
from issuer.schema import IssuerType
from mainsite.mixins import StaffResolverMixin, ImageResolverMixin, PermissionsResolverMixin
from staff.schema import InstitutionStaffType, FacultyStaffType, PermissionType


class FacultyType(PermissionsResolverMixin, StaffResolverMixin, DjangoObjectType):

    class Meta:
        model = Faculty
        fields = ('name', 'entity_id', 'institution', 'created_at', 'description')

    issuers = graphene.List(IssuerType)
    staff = graphene.List(FacultyStaffType)
    permissions = graphene.Field(PermissionType)

    def resolve_issuers(self, info):
        return self.get_issuers(info.context.user, ['may_read'])


class InstitutionType(PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin, DjangoObjectType):

    class Meta:
        model = Institution
        fields = ('entity_id', 'name', 'staff', 'created_at', 'description', 'image', 'grading_table', 'brin')

    faculties = graphene.List(FacultyType)
    staff = graphene.List(InstitutionStaffType)
    permissions = graphene.Field(PermissionType)

    def resolve_faculties(self, info):
        return self.get_faculties(info.context.user, ['may_read'])


class Query(object):
    institutions = graphene.List(InstitutionType)
    faculties = graphene.List(FacultyType)
    faculty = graphene.Field(FacultyType, id=graphene.String())

    def resolve_institutions(self, info, **kwargs):
        return [inst for inst in Institution.objects.all() if inst.has_permissions(info.context.user, ['may_read'])]

    def resolve_faculties(self, info, **kwargs):
        return [fac for fac in Faculty.objects.all() if fac.has_permissions(info.context.user, ['may_read'])]

    def resolve_faculty(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            faculty = Faculty.objects.get(entity_id=id)
            if faculty.has_permissions(info.context.user, ['may_read']):
                return faculty
