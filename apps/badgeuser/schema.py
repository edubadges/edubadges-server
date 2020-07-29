import graphene
from graphene_django.types import DjangoObjectType

from badgeuser.models import BadgeUser, Terms, TermsAgreement
from institution.schema import InstitutionType
from mainsite.exceptions import GraphQLException
from staff.schema import InstitutionStaffType, FacultyStaffType, IssuerStaffType, BadgeClassStaffType
from mainsite.graphql_utils import UserProvisionmentType, resolver_blocker_only_for_current_user, resolver_blocker_for_students
from lti_edu.schema import StudentsEnrolledType


class TermsType(DjangoObjectType):

    class Meta:
        model = Terms
        fields = ('entity_id', 'url', 'language', 'terms_type', 'version', 'institution')

    institution = graphene.Field(InstitutionType)


class TermsAgreementType(DjangoObjectType):

    class Meta:
        model = TermsAgreement
        fields = ('agreed', 'agreed_version', 'terms')

    terms = graphene.Field(TermsType)


class BadgeUserType(DjangoObjectType):

    class Meta:
        model = BadgeUser
        fields = ('first_name', 'last_name', 'email', 'date_joined', 'entity_id', 'userprovisionments')

    institution = graphene.Field(InstitutionType)
    institution_staff = graphene.Field(InstitutionStaffType)
    faculty_staffs = graphene.List(FacultyStaffType)
    issuer_staffs = graphene.List(IssuerStaffType)
    badgeclass_staffs = graphene.List(BadgeClassStaffType)
    userprovisionments = graphene.List(UserProvisionmentType)
    pending_enrollments = graphene.List(StudentsEnrolledType)
    terms_agreements = graphene.List(TermsAgreementType)

    def resolve_institution_staff(self, info):
        return self.cached_institution_staff()

    def resolve_faculty_staffs(self, info):
        return self.cached_faculty_staffs()

    def resolve_issuer_staffs(self, info):
        return self.cached_issuer_staffs()

    def resolve_badgeclass_staffs(self, info):
        return self.cached_badgeclass_staffs()

    @resolver_blocker_only_for_current_user
    def resolve_userprovisionments(self, info):
        return list(self.userprovisionment_set.all())

    @resolver_blocker_only_for_current_user
    def resolve_pending_enrollments(self, info):
        return info.context.user.cached_pending_enrollments()

    @resolver_blocker_only_for_current_user
    def resolve_terms_agreements(self, info):
        return info.context.user.cached_terms_agreements()


class Query(object):
    current_user = graphene.Field(BadgeUserType)
    users = graphene.List(BadgeUserType)
    user = graphene.Field(BadgeUserType, id=graphene.String())

    def resolve_user(self, info, **kwargs):
        user = BadgeUser.objects.get(entity_id=kwargs.get('id'))
        if info.context.user.institution != user.institution:
            raise GraphQLException('Cannot query user outside your institution')
        return user

    @resolver_blocker_for_students
    def resolve_users(self, info, **kwargs):
        return info.context.user.cached_colleagues()

    def resolve_current_user(self, info, **kwargs):
        return info.context.user
