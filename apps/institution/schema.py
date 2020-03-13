import graphene
from graphene_django.types import DjangoObjectType
from .models import Institution, Faculty
from issuer.schema import IssuerType
from mainsite.mixins import StaffResolverMixin
from staff.schema import InstitutionStaffType, FacultyStaffType


class FacultyType(StaffResolverMixin, DjangoObjectType):

    class Meta:
        model = Faculty
        fields = ('name', 'entity_id', 'institution')

    issuers = graphene.List(IssuerType)
    staff = graphene.List(FacultyStaffType)

    def resolve_issuers(self, info):
        return self.get_issuers(info.context.user, ['may_read'])


class InstitutionType(StaffResolverMixin, DjangoObjectType):

    class Meta:
        model = Institution
        fields = ('name',)

    faculties = graphene.List(FacultyType)
    staff = graphene.List(InstitutionStaffType)

    def resolve_faculties(self, info):
        return self.get_faculties(info.context.user, ['may_read'])


class Query(object):
    institutions = graphene.List(InstitutionType)
    faculties = graphene.List(FacultyType)
    institution = graphene.Field(InstitutionType, id=graphene.ID())
    faculty = graphene.Field(FacultyType, id=graphene.ID())

    def resolve_institutions(self, info, **kwargs):
        return [inst for inst in Institution.objects.all() if inst.has_permissions(info.context.user, ['may_read'])]

    def resolve_institution(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            institution = Institution.objects.get(id=id)
            if institution.has_permissions(info.context.user, ['may_read']):
                return institution

    def resolve_faculties(self, info, **kwargs):
        return [fac for fac in Faculty.objects.all() if fac.has_permissions(info.context.user, ['may_read'])]

    def resolve_faculty(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            faculty = Faculty.objects.get(id=id)
            if faculty.has_permissions(info.context.user, ['may_read']):
                return faculty