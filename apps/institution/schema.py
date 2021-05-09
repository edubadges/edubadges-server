import graphene
from graphene_django.types import DjangoObjectType

from issuer.schema import IssuerType
from mainsite.graphql_utils import UserProvisionmentResolverMixin, ContentTypeIdResolverMixin, StaffResolverMixin, \
    ImageResolverMixin, PermissionsResolverMixin, DefaultLanguageResolverMixin
from mainsite.utils import generate_image_url
from staff.schema import InstitutionStaffType, FacultyStaffType
from .models import Institution, Faculty


class FacultyType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin,
                  ContentTypeIdResolverMixin, DefaultLanguageResolverMixin, DjangoObjectType):
    class Meta:
        model = Faculty
        fields = ('name_english', 'name_dutch', 'entity_id', 'institution', 'created_at', 'description_english',
                  'description_dutch',
                  'content_type_id')

    issuers = graphene.List(IssuerType)
    issuer_count = graphene.Int()
    pending_enrollment_count = graphene.Int()
    public_issuers = graphene.List(IssuerType)
    staff = graphene.List(FacultyStaffType)
    name = graphene.String()
    has_unrevoked_assertions = graphene.Boolean()

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


class InstitutionType(UserProvisionmentResolverMixin, PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin,
                      ContentTypeIdResolverMixin, DefaultLanguageResolverMixin, DjangoObjectType):
    class Meta:
        model = Institution
        fields = ('entity_id', 'identifier', 'name_english', 'name_dutch', 'staff', 'created_at', 'description_english',
                  'description_dutch', 'institution_type', 'image_english', 'image_dutch', 'grading_table', 'brin',
                  'content_type_id', 'grondslag_formeel', 'grondslag_informeel', 'default_language',
                  'direct_awarding_enabled', 'award_allow_all_institutions')

    faculties = graphene.List(FacultyType)
    public_faculties = graphene.List(FacultyType)
    staff = graphene.List(InstitutionStaffType)
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

    def resolve_faculties(self, info):
        return self.get_faculties(info.context.user, ['may_read'])

    def resolve_public_faculties(self, info):
        return self.cached_faculties()

    def resolve_award_allowed_institutions(self, info):
        institutions = Institution.objects.all() if self.award_allow_all_institutions else self.award_allowed_institutions.all()
        return [institution.identifier for institution in institutions]


class Query(object):
    public_institution = graphene.Field(InstitutionType, id=graphene.String())
    current_institution = graphene.Field(InstitutionType)
    institutions = graphene.List(InstitutionType)
    public_institutions = graphene.List(InstitutionType)
    faculties = graphene.List(FacultyType)
    faculty = graphene.Field(FacultyType, id=graphene.String())

    def resolve_current_institution(self, info, **kwargs):
        return info.context.user.institution

    def resolve_institutions(self, info, **kwargs):
        return [inst for inst in Institution.objects.all() if inst.has_permissions(info.context.user, ['may_read'])]

    def resolve_public_institution(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            institution = Institution.objects.get(entity_id=id)
            return institution

    def resolve_public_institutions(self, info, **kwargs):
        return Institution.objects.all()

    def resolve_faculties(self, info, **kwargs):
        return [fac for fac in Faculty.objects.all() if fac.has_permissions(info.context.user, ['may_read'])]

    def resolve_faculty(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            faculty = Faculty.objects.get(entity_id=id)
            if faculty.has_permissions(info.context.user, ['may_read']):
                return faculty
