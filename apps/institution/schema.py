import graphene
from graphene_django.types import DjangoObjectType

from issuer.schema import IssuerType
from mainsite.graphql_utils import UserProvisionmentResolverMixin, ContentTypeIdResolverMixin, StaffResolverMixin, \
    ImageResolverMixin, PermissionsResolverMixin
from staff.schema import InstitutionStaffType, FacultyStaffType
from .models import Institution, Faculty


class FacultyType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin,
                  ContentTypeIdResolverMixin, DjangoObjectType):
    class Meta:
        model = Faculty
        fields = ('name', 'entity_id', 'institution', 'created_at', 'description', 'content_type_id')

    issuers = graphene.List(IssuerType)
    staff = graphene.List(FacultyStaffType)

    def resolve_issuers(self, info):
        return self.get_issuers(info.context.user, ['may_read'])


class InstitutionType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin,
                      ContentTypeIdResolverMixin, DjangoObjectType):
    class Meta:
        model = Institution
        fields = ('entity_id', 'name', 'staff', 'created_at', 'description',
                  'image', 'grading_table', 'brin', 'content_type_id')

    faculties = graphene.List(FacultyType)
    staff = graphene.List(InstitutionStaffType)

    def resolve_faculties(self, info):
        return self.get_faculties(info.context.user, ['may_read'])


class Query(object):
    current_institution = graphene.Field(InstitutionType)
    institutions = graphene.List(InstitutionType)
    faculties = graphene.List(FacultyType)
    faculty = graphene.Field(FacultyType, id=graphene.String())

    def resolve_current_institution(self, info, **kwargs):
        return info.context.user.institution

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
