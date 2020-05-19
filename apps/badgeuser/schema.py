import graphene
from graphene_django.types import DjangoObjectType
from badgeuser.models import BadgeUser
from institution.schema import InstitutionType
from mainsite.exceptions import GraphQLException
from staff.schema import InstitutionStaffType, FacultyStaffType, IssuerStaffType, BadgeClassStaffType


class BadgeUserType(DjangoObjectType):

    class Meta:
        model = BadgeUser
        fields = ('first_name', 'last_name', 'email', 'date_joined', 'entity_id')

    institution = graphene.Field(InstitutionType)
    institution_staff = graphene.Field(InstitutionStaffType)
    faculty_staffs = graphene.List(FacultyStaffType)
    issuer_staffs = graphene.List(IssuerStaffType)
    badgeclass_staffs = graphene.List(BadgeClassStaffType)

    def resolve_institution_staff(self, info):
        return self.cached_institution_staff()

    def resolve_faculty_staffs(self, info):
        return self.cached_faculty_staffs()

    def resolve_issuer_staffs(self, info):
        return self.cached_issuer_staffs()

    def resolve_badgeclass_staffs(self, info):
        return self.cached_badgeclass_staffs()


class Query(object):
    current_user = graphene.Field(BadgeUserType)
    users = graphene.List(BadgeUserType)
    user = graphene.Field(BadgeUserType, id=graphene.String())

    def resolve_user(self, info, **kwargs):
        user = BadgeUser.objects.get(entity_id=kwargs.get('id'))
        if info.context.user.institution != user.institution:
            raise GraphQLException('Cannot query user outside your institution')
        return user

    def resolve_users(self, info, **kwargs):
        return [staff.cached_user for staff in info.context.user.institution.cached_staff()]

    def resolve_current_user(self, info, **kwargs):
        return info.context.user
