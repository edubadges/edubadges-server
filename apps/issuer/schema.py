import graphene
from graphene.relay import ConnectionField
from graphene_django.types import DjangoObjectType, Connection

from directaward.schema import DirectAwardType, DirectAwardBundleType
from lti_edu.schema import StudentsEnrolledType
from mainsite.graphql_utils import JSONType, UserProvisionmentResolverMixin, ContentTypeIdResolverMixin, \
    StaffResolverMixin, ImageResolverMixin, PermissionsResolverMixin, resolver_blocker_for_students, \
    DefaultLanguageResolverMixin, resolver_blocker_only_for_current_user
from mainsite.utils import generate_image_url
from staff.schema import IssuerStaffType, BadgeClassStaffType
from .models import Issuer, BadgeClass, BadgeInstance, BadgeClassExtension, IssuerExtension, BadgeInstanceExtension, \
    BadgeClassAlignment, BadgeClassTag, BadgeInstanceEvidence, BadgeInstanceCollection


class ExtensionResolverMixin(object):

    def resolve_extensions(self, info):
        return self.cached_extensions()


class ExtensionTypeMetaMixin(object):
    fields = ('name', 'original_json')


class BaseExtensionMixin(object):

    def resolve_original_json(self, info):
        return self.original_json


class IssuerExtensionType(BaseExtensionMixin, DjangoObjectType):
    class Meta(ExtensionTypeMetaMixin):
        model = IssuerExtension


class BadgeClassExtensionType(BaseExtensionMixin, DjangoObjectType):
    class Meta(ExtensionTypeMetaMixin):
        model = BadgeClassExtension


class BadgeInstanceExtensionType(BaseExtensionMixin, DjangoObjectType):
    class Meta(ExtensionTypeMetaMixin):
        model = BadgeInstanceExtension


class BadgeClassAlignmentType(DjangoObjectType):
    class Meta:
        model = BadgeClassAlignment
        fields = ('target_name', 'original_json', 'target_url',
                  'target_description', 'target_framework', 'target_code')


class BadgeInstanceEvidenceType(DjangoObjectType):
    class Meta:
        model = BadgeInstanceEvidence
        fields = ('evidence_url', 'narrative', 'name', 'description')


class BadgeClassTagType(DjangoObjectType):
    class Meta:
        model = BadgeClassTag
        fields = ('name',)


def badge_class_type():
    from issuer.schema import BadgeClassType
    return BadgeClassType


class IssuerType(ContentTypeIdResolverMixin, PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin,
                 ExtensionResolverMixin, UserProvisionmentResolverMixin, DefaultLanguageResolverMixin,
                 DjangoObjectType):
    class Meta:
        model = Issuer
        fields = ('entity_id',
                  'badgeclasses', 'faculty',
                  'name_english', 'name_dutch',
                  'image_dutch', 'image_english',
                  'url_english', 'url_dutch',
                  'description_english', 'description_dutch',
                  'email', 'created_at', 'content_type_id', 'public_url')

    staff = graphene.List(IssuerStaffType)
    public_badgeclasses = graphene.List(badge_class_type)
    assertion_count = graphene.Int()
    badgeclass_count = graphene.Int()
    badgeclasses_count = graphene.Int()
    pending_enrollment_count = graphene.Int()
    extensions = graphene.List(IssuerExtensionType)
    public_url = graphene.String()
    name = graphene.String()
    image = graphene.String()
    description = graphene.String()
    url = graphene.String()

    def resolve_image_english(self, info):
        return generate_image_url(self.image_english)

    def resolve_image_dutch(self, info):
        return generate_image_url(self.image_dutch)

    def resolve_image(self, info):
        return generate_image_url(self.image)

    def resolve_name(self, info):
        return self.name

    def resolve_url(self, info):
        return self.url

    def resolve_description(self, info):
        return self.description

    def resolve_assertion_count(self, info):
        return self.cached_assertions().__len__()

    def resolve_badgeclasses(self, info):
        return self.get_badgeclasses(info.context.user, ['may_read'])

    def resolve_badgeclass_count(self, info):
        return self.get_badgeclasses(info.context.user, ['may_read']).__len__()

    def resolve_public_badgeclasses(self, info):
        return [bc for bc in self.cached_badgeclasses() if not bc.is_private]

    def resolve_badgeclasses_count(self, info):
        return self.badgeclasses_count

    def resolve_pending_enrollment_count(self, info):
        return self.cached_pending_enrollments().__len__()


def badge_user_type():
    from badgeuser.schema import BadgeUserType
    return BadgeUserType


def terms_type():
    from badgeuser.schema import TermsType
    return TermsType


class BadgeInstanceType(ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):
    share_url = graphene.String()
    extensions = graphene.List(BadgeInstanceExtensionType)
    user = graphene.Field(badge_user_type)
    validation = graphene.Field(JSONType)
    evidences = graphene.List(BadgeInstanceEvidenceType)

    class Meta:
        model = BadgeInstance
        fields = ('id', 'entity_id', 'badgeclass', 'identifier', 'image', 'updated_at',
                  'recipient_identifier', 'recipient_type', 'revoked', 'issued_on',
                  'revocation_reason', 'expires_at', 'acceptance', 'created_at',
                  'public', 'award_type')

    def resolve_validation(self, info, **kwargs):
        return self.validate()

    def resolve_evidences(self, info, **kwargs):
        return self.cached_evidence()


class BadgeInstanceCollectionType(DjangoObjectType,):

    badge_instances = graphene.List(BadgeInstanceType)
    public_badge_instances = graphene.List(BadgeInstanceType)

    class Meta:
        model = BadgeInstanceCollection
        fields = ('id', 'entity_id', 'name', 'description', 'public', 'updated_at', 'created_at')

    @resolver_blocker_only_for_current_user
    def resolve_badge_instances(self, info, **kwargs):
        return list(BadgeInstance.objects.filter(badgeinstancecollection=self))

    def resolve_public_badge_instances(self, info, **kwargs):
        return list(BadgeInstance.objects.filter(badgeinstancecollection=self, public=True, revoked=False))

class BadgeInstanceConnection(Connection):
    class Meta:
        node = BadgeInstanceType


class BadgeClassType(ContentTypeIdResolverMixin, PermissionsResolverMixin, StaffResolverMixin,
                     UserProvisionmentResolverMixin, ImageResolverMixin, ExtensionResolverMixin,
                     DefaultLanguageResolverMixin, DjangoObjectType):
    class Meta:
        model = BadgeClass
        fields = ('name', 'entity_id', 'issuer', 'image', 'staff',
                  'description', 'criteria_url', 'criteria_text', 'is_private',
                  'created_at', 'expiration_period', 'public_url', 'assertions_count',
                  'content_type_id', 'formal', 'evidence_required', 'narrative_required')

    direct_awards = graphene.List(DirectAwardType)
    direct_award_bundles = graphene.List(DirectAwardBundleType)
    staff = graphene.List(BadgeClassStaffType)
    extensions = graphene.List(BadgeClassExtensionType)
    tags = graphene.List(BadgeClassTagType)
    alignments = graphene.List(BadgeClassAlignmentType)
    enrollments = graphene.List(StudentsEnrolledType)
    pending_enrollments = graphene.List(StudentsEnrolledType)
    pending_enrollments_including_denied = graphene.List(StudentsEnrolledType)
    badge_assertions = graphene.List(BadgeInstanceType)
    assertions_paginated = ConnectionField(BadgeInstanceConnection)
    assertion_count = graphene.Int()
    pending_enrollment_count = graphene.Int()
    expiration_period = graphene.Int()
    assertions_count = graphene.Int()
    is_private = graphene.Boolean()
    public_url = graphene.String()
    terms = graphene.Field(terms_type())
    award_allowed_institutions = graphene.List(graphene.String)

    def resolve_terms(self, info, **kwargs):
        return self._get_terms()

    def resolve_tags(self, info, **kwargs):
        return self.cached_tags()

    def resolve_alignments(self, info, **kwargs):
        return self.cached_alignments()

    @resolver_blocker_for_students
    def resolve_direct_awards(self, info, **kwargs):
        return self.cached_direct_awards()

    @resolver_blocker_for_students
    def resolve_direct_award_bundles(self, info, **kwargs):
        return self.cached_direct_award_bundles()

    @resolver_blocker_for_students
    def resolve_enrollments(self, info, **kwargs):
        return self.cached_enrollments()

    @resolver_blocker_for_students
    def resolve_pending_enrollments(self, info, **kwargs):
        return self.cached_pending_enrollments()

    def resolve_pending_enrollments_including_denied(self, info, **kwargs):
        return self.cached_pending_enrollments_including_denied()

    @resolver_blocker_for_students
    def resolve_pending_enrollment_count(self, info, **kwargs):
        return self.cached_pending_enrollments().__len__()

    @resolver_blocker_for_students
    def resolve_badge_assertions(self, info, **kwargs):
        return self.assertions

    @resolver_blocker_for_students
    def resolve_assertions_paginated(self, info, **kwargs):
        return self.assertions

    @resolver_blocker_for_students
    def resolve_assertion_count(self, info, **kwargs):
        return self.assertions.__len__()

    def resolve_expiration_period(self, info, **kwargs):
        if self.expiration_period:
            return self.expiration_period.days

    def resolve_assertions_count(self, info):
        return self.assertions_count

    def resolve_award_allowed_institutions(self, info):
        return [institution.identifier for institution in self.award_allowed_institutions.all()]


class Query(object):
    issuers = graphene.List(IssuerType)
    badge_classes = graphene.List(BadgeClassType)
    badge_classes_to_award = graphene.List(BadgeClassType)
    public_badge_classes = graphene.List(BadgeClassType)
    badge_instances = graphene.List(BadgeInstanceType)
    revoked_badge_instances = graphene.List(BadgeInstanceType)
    badge_instance_collections = graphene.List(BadgeInstanceCollectionType)
    issuer = graphene.Field(IssuerType, id=graphene.String())
    public_issuer = graphene.Field(IssuerType, id=graphene.String())
    badge_class = graphene.Field(BadgeClassType, id=graphene.String(), days=graphene.Int())
    badge_instance = graphene.Field(BadgeInstanceType, id=graphene.String())
    badge_instance_collection = graphene.Field(BadgeInstanceCollectionType, id=graphene.String())
    badge_instances_count = graphene.Int()
    badge_classes_count = graphene.Int()

    def resolve_issuers(self, info, **kwargs):
        return [issuer for issuer in Issuer.objects.filter(archived=False)
                if issuer.has_permissions(info.context.user, ['may_read'])]

    def resolve_issuer(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            issuer = Issuer.objects.get(entity_id=id, archived=False)
            if issuer.has_permissions(info.context.user, ['may_read']):
                return issuer

    def resolve_public_issuer(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            issuer = Issuer.objects.get(entity_id=id, archived=False)
            return issuer

    def resolve_badge_classes(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.filter(archived=False)
                if bc.has_permissions(info.context.user, ['may_read'])]

    def resolve_badge_classes_to_award(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.filter(archived=False)
                if bc.has_permissions(info.context.user, ['may_award'])]

    def resolve_public_badge_classes(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.filter(archived=False, is_private=False)]

    def resolve_badge_class(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeClass.objects.get(entity_id=id, archived=False)
            # Student's who are logged in need to access this to start the enrollment
            if (hasattr(info.context.user, 'is_student') and info.context.user.is_student) or bc.has_permissions(info.context.user, ['may_read']):
                return bc

    def resolve_badge_instance(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeInstance.objects.get(entity_id=id)
            if bc.user_id == info.context.user.id:
                return bc

    def resolve_badge_instance_collection(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeInstanceCollection.objects.get(entity_id=id)
            # Called anonymous in public collection page
            if bc.public or bc.user_id == info.context.user.id:
                return bc

    def resolve_badge_instance_collections(self, info, **kwargs):
        return BadgeInstanceCollection.objects.filter(user=info.context.user)

    def resolve_badge_instances(self, info, **kwargs):
        return info.context.user.cached_badgeinstances()

    def resolve_revoked_badge_instances(self, info, **kwargs):
        return list(filter(lambda bi: bi.revoked == True, info.context.user.cached_badgeinstances()))

    def resolve_badge_instances_count(self, info):
        return BadgeInstance.objects.count()

    def resolve_badge_classes_count(self, info):
        return BadgeClass.objects.count()
