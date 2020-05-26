import json

import graphene
from graphene_django.types import DjangoObjectType

from lti_edu.schema import StudentsEnrolledType
from mainsite.graphql_utils import JSONType, UserProvisionmentResolverMixin, ContentTypeIdResolverMixin, \
    StaffResolverMixin, ImageResolverMixin, PermissionsResolverMixin, resolver_blocker_for_students
from staff.schema import IssuerStaffType, BadgeClassStaffType, PermissionType
from .models import Issuer, BadgeClass, BadgeInstance, BadgeClassExtension, IssuerExtension, BadgeInstanceExtension, \
    BadgeClassAlignment, BadgeClassTag


class ExtensionResolverMixin(object):

    permissions = graphene.Field(PermissionType)

    def resolve_extensions(self, info):
        return self.cached_extensions()


class ExtensionTypeMetaMixin(object):
    fields = ('name', 'original_json')


class BaseExtensionMixin(object):

    def resolve_original_json(self, info):
        return json.loads(self.original_json)


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


class BadgeClassTagType(DjangoObjectType):
    class Meta:
        model = BadgeClassTag
        fields = ('name',)


class IssuerType(ContentTypeIdResolverMixin, PermissionsResolverMixin, StaffResolverMixin, ImageResolverMixin,
                 ExtensionResolverMixin, UserProvisionmentResolverMixin, DjangoObjectType):
    class Meta:
        model = Issuer
        fields = ('name', 'entity_id', 'badgeclasses', 'faculty',
                  'image', 'description', 'url', 'email', 'created_at',
                  'content_type_id')

    staff = graphene.List(IssuerStaffType)
    badgeclasses_count = graphene.Int()
    extensions = graphene.List(IssuerExtensionType)

    def resolve_badgeclasses(self, info):
        return self.get_badgeclasses(info.context.user, ['may_read'])

    def resolve_badgeclasses_count(self, info):
        return len(self.get_badgeclasses(info.context.user, ['read']))


def badge_user_type():
    from badgeuser.schema import BadgeUserType
    return BadgeUserType


class BadgeInstanceType(ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):
    share_url = graphene.String()
    extensions = graphene.List(BadgeInstanceExtensionType)
    user = graphene.Field(badge_user_type)
    validation = graphene.Field(JSONType)

    class Meta:
        model = BadgeInstance
        fields = ('entity_id', 'badgeclass', 'identifier', 'image',
                  'recipient_identifier', 'recipient_type', 'revoked', 'issued_on',
                  'revocation_reason', 'expires_at', 'acceptance', 'created_at',
                  'public')

    def resolve_validation(self, info, **kwargs):
        return self.validate()


class BadgeClassType(ContentTypeIdResolverMixin, PermissionsResolverMixin, StaffResolverMixin,
                     UserProvisionmentResolverMixin, ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):
    class Meta:
        model = BadgeClass
        fields = ('name', 'entity_id', 'issuer', 'image', 'staff',
                  'description', 'criteria_url', 'criteria_text',
                  'created_at', 'expiration_period', 'public_url',
                  'content_type_id')

    staff = graphene.List(BadgeClassStaffType)
    extensions = graphene.List(BadgeClassExtensionType)
    tags = graphene.List(BadgeClassTagType)
    alignments = graphene.List(BadgeClassAlignmentType)
    enrollments = graphene.List(StudentsEnrolledType)
    pending_enrollments = graphene.List(StudentsEnrolledType)
    badge_assertions = graphene.List(BadgeInstanceType)
    expiration_period = graphene.Int()
    public_url = graphene.String()

    def resolve_tags(self, info, **kwargs):
        return self.cached_tags()

    def resolve_alignments(self, info, **kwargs):
        return self.cached_alignments()

    @resolver_blocker_for_students
    def resolve_enrollments(self, info, **kwargs):
        return self.cached_enrollments()

    @resolver_blocker_for_students
    def resolve_pending_enrollments(self, info, **kwargs):
        return self.cached_pending_enrollments()

    @resolver_blocker_for_students
    def resolve_badge_assertions(self, info, **kwargs):
        return self.assertions

    def resolve_expiration_period(self, info, **kwargs):
        if self.expiration_period:
            return self.expiration_period.days


class Query(object):
    issuers = graphene.List(IssuerType)
    badge_classes = graphene.List(BadgeClassType)
    badge_instances = graphene.List(BadgeInstanceType)
    issuer = graphene.Field(IssuerType, id=graphene.String())
    badge_class = graphene.Field(BadgeClassType, id=graphene.String())
    badge_instance = graphene.Field(BadgeInstanceType, id=graphene.String())

    def resolve_issuers(self, info, **kwargs):
        return [issuer for issuer in Issuer.objects.all() if issuer.has_permissions(info.context.user, ['may_read'])]

    def resolve_issuer(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            issuer = Issuer.objects.get(entity_id=id)
            if issuer.has_permissions(info.context.user, ['may_read']):
                return issuer

    def resolve_badge_classes(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.all() if bc.has_permissions(info.context.user, ['may_read'])]

    def resolve_badge_class(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeClass.objects.get(entity_id=id)
            if bc.has_permissions(info.context.user, ['may_read']):
                return bc

    def resolve_badge_instance(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeInstance.objects.get(entity_id=id)
            if bc.user_id == info.context.user.id:
                return bc

    def resolve_badge_instances(self, info, **kwargs):
        return list(info.context.user.cached_badgeinstances())
