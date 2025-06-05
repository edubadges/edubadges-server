import graphene
from graphene_django.types import DjangoObjectType

from issuer.models import Issuer
from issuer.schema import IssuerType
from mainsite.graphql_utils import UserProvisionmentResolverMixin, ContentTypeIdResolverMixin, StaffResolverMixin, \
    ImageResolverMixin, PermissionsResolverMixin, DefaultLanguageResolverMixin
from mainsite.utils import generate_image_url
from staff.schema import InstitutionStaffType, FacultyStaffType
from .models import Institution, Faculty, BadgeClassTag


class FacultyType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin,
                  ImageResolverMixin, ContentTypeIdResolverMixin, DefaultLanguageResolverMixin, DjangoObjectType):
    class Meta:
        model = Faculty
        fields = ('name_english', 'name_dutch', 'entity_id', 'institution', 'created_at', 'description_english',
                  'description_dutch', 'content_type_id', 'on_behalf_of', 'on_behalf_of_url', 'archived',
                  'on_behalf_of_display_name', 'faculty_type', 'image_english', 'image_dutch',
                  'linkedin_org_identifier', 'visibility_type')

    issuers = graphene.List(IssuerType)
    issuer_count = graphene.Int()
    pending_enrollment_count = graphene.Int()
    public_issuers = graphene.List(IssuerType)
    staff = graphene.List(FacultyStaffType)
    name = graphene.String()
    image = graphene.String()
    has_assertions = graphene.Boolean()
    has_unrevoked_assertions = graphene.Boolean()

    def resolve_image_english(self, info):
        return generate_image_url(self.image_english)

    def resolve_image_dutch(self, info):
        return generate_image_url(self.image_dutch)

    def resolve_image(self, info):
        return generate_image_url(self.image)

    def resolve_name(self, info):
        return self.name

    def resolve_issuers(self, info):
        return self.get_issuers(info.context.user, ['may_read'])

    def resolve_issuer_count(self, info):
        return self.get_issuers(info.context.user, ['may_read']).__len__()

    def resolve_pending_enrollment_count(self, info):
        return self.cached_pending_enrollments().__len__()

    def resolve_public_issuers(self, info):
        return self.cached_issuers()

    def resolve_has_unrevoked_assertions(self, info):
        return any([assertion.revoked is False for assertion in self.assertions])

    def resolve_has_assertions(self, info):
        return bool(self.assertions)

class BadgeClassTagType(DjangoObjectType):
    class Meta:
        model = BadgeClassTag
        fields = ('id', 'name', 'archived')

def terms_type():
    from badgeuser.schema import TermsType
    return TermsType

class InstitutionType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin,
                      ContentTypeIdResolverMixin, DefaultLanguageResolverMixin, DjangoObjectType):
    class Meta:
        model = Institution
        fields = ('entity_id', 'identifier', 'name_english', 'name_dutch', 'staff', 'created_at', 'description_english',
                  'description_dutch', 'institution_type', 'image_english', 'image_dutch', 'grading_table', 'brin',
                  'content_type_id', 'grondslag_formeel', 'grondslag_informeel', 'default_language', 'id', 'email',
                  'direct_awarding_enabled', 'award_allow_all_institutions', 'lti_enabled', 'alternative_identifier',
                  'eppn_reg_exp_format', 'linkedin_org_identifier', 'sis_integration_enabled', 'ob3_ssi_agent_enabled',
                  'micro_credentials_enabled', 'country_code', 'virtual_organization_allowed')

    faculties = graphene.List(FacultyType)
    public_faculties = graphene.List(FacultyType)
    staff = graphene.List(InstitutionStaffType)
    tags = graphene.List(BadgeClassTagType)
    terms = graphene.List(terms_type())
    image = graphene.String()
    name = graphene.String()
    award_allowed_institutions = graphene.List(graphene.String)

    def resolve_image_english(self, info):
        return generate_image_url(self.image_english)

    def resolve_image_dutch(self, info):
        return generate_image_url(self.image_dutch)

    def resolve_name(self, info):
        return self.name

    def resolve_image(self, info):
        return generate_image_url(self.image)

    def resolve_tags(self, info):
        return list(self.badgeclasstag_set.all())

    def resolve_faculties(self, info):
        return self.get_faculties(info.context.user, ['may_read'])

    def resolve_public_faculties(self, info):
        faculties = self.cached_faculties()
        return [faculty for faculty in faculties if
                faculty.visibility_type is None or faculty.visibility_type == Faculty.VISIBILITY_PUBLIC]

    def resolve_award_allowed_institutions(self, info):
        institutions = Institution.objects.all() if self.award_allow_all_institutions else self.award_allowed_institutions.all()
        return [institution.identifier for institution in institutions]

    def resolve_terms(self, info):
        return self.cached_terms()


class Query(object):
    public_institution = graphene.Field(InstitutionType, id=graphene.String())
    current_institution = graphene.Field(InstitutionType)
    institutions = graphene.List(InstitutionType)
    public_institutions = graphene.List(InstitutionType)
    public_faculty = graphene.Field(FacultyType, id=graphene.String())
    faculties = graphene.List(FacultyType)
    issuers = graphene.List(IssuerType)
    faculty = graphene.Field(FacultyType, id=graphene.String())

    def resolve_current_institution(self, info, **kwargs):
        return info.context.user.institution

    def resolve_issuers(self, info, **kwargs):
        user = info.context.user
        return [iss for iss in Issuer.objects.filter(faculty__institution=user.institution) if
                iss.has_permissions(user, ['may_update'])]

    def resolve_institutions(self, info, **kwargs):
        is_superuser = hasattr(info.context.user, 'is_superuser') and info.context.user.is_superuser
        return [inst for inst in Institution.objects.all() if
                inst.has_permissions(info.context.user, ['may_read']) or is_superuser]

    def resolve_public_institution(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            institution = Institution.objects.get(entity_id=id)
            return institution

    def resolve_public_institutions(self, info, **kwargs):
        return Institution.objects.filter(public_institution=True).all()

    def resolve_public_faculty(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Faculty.objects.get(entity_id=id)

    def resolve_faculties(self, info, **kwargs):
        return [fac for fac in Faculty.objects.all() if fac.has_permissions(info.context.user, ['may_read'])]

    def resolve_faculty(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            faculty = Faculty.objects.get(entity_id=id)
            if faculty.has_permissions(info.context.user, ['may_read']):
                return faculty
