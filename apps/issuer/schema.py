import graphene
from graphene_django.types import DjangoObjectType
from .models import Issuer, BadgeClass, BadgeInstance, BadgeClassExtension, IssuerExtension, BadgeInstanceExtension, \
                    BadgeClassAlignment, BadgeClassTag
from mainsite.mixins import StaffResolverMixin
from staff.schema import IssuerStaffType, BadgeClassStaffType


class ImageResolverMixin(object):

    def resolve_image(self, info):
        return self.image_url()


class ExtensionResolverMixin(object):

    def resolve_extensions(self, info):
        return self.cached_extensions()


class ExtensionTypeMetaMixin(object):

    fields = ('name', 'original_json')


class IssuerExtensionType(DjangoObjectType):

    class Meta(ExtensionTypeMetaMixin):
        model = IssuerExtension


class BadgeClassExtensionType(DjangoObjectType):

    class Meta(ExtensionTypeMetaMixin):
        model = BadgeClassExtension


class BadgeInstanceExtensionType(DjangoObjectType):
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


class IssuerType(StaffResolverMixin, ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):

    class Meta:
        model = Issuer
        fields = ('name', 'entity_id', 'badgeclasses', 'faculty',
                  'image', 'description', 'url', 'email')

    staff = graphene.List(IssuerStaffType)
    badgeclasses_count = graphene.Int()
    extensions = graphene.List(IssuerExtensionType)

    def resolve_badgeclasses(self, info):
        return self.get_badgeclasses(info.context.user, ['may_read'])

    def resolve_badgeclasses_count(self, info):
        return len(self.get_badgeclasses(info.context.user, ['read']))


class BadgeClassType(StaffResolverMixin, ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):

    class Meta:
        model = BadgeClass
        fields = ('name', 'entity_id', 'issuer', 'image', 'staff',
                  'description', 'criteria_url', 'criteria_text',)

    staff = graphene.List(BadgeClassStaffType)
    extensions = graphene.List(BadgeClassExtensionType)
    tags = graphene.List(BadgeClassTagType)
    alignments = graphene.List(BadgeClassAlignmentType)

    def resolve_tags(self, info, **kwargs):
        return self.cached_tags()

    def resolve_alignments(self, info, **kwargs):
        return self.cached_alignments()


class BadgeInstanceType(ImageResolverMixin, ExtensionResolverMixin, DjangoObjectType):

    share_url = graphene.String()
    extensions = graphene.List(BadgeInstanceExtensionType)

    class Meta:
        model = BadgeInstance
        fields = ('entity_id', 'badgeclass', 'identifier', 'image',
                  'recipient_identifier', 'recipient_type', 'revoked',
                  'revocation_reason', 'expires_at', 'acceptance',
                  'narrative', 'public')


class Query(object):
    issuers = graphene.List(IssuerType)
    badge_classes = graphene.List(BadgeClassType)
    badge_instances = graphene.List(BadgeInstanceType)
    issuer = graphene.Field(IssuerType, id=graphene.ID())
    badge_class = graphene.Field(BadgeClassType, id=graphene.ID())
    badge_instance = graphene.Field(BadgeInstanceType, id=graphene.ID())

    def resolve_issuers(self, info, **kwargs):
        return [issuer for issuer in Issuer.objects.all() if issuer.has_permissions(info.context.user, ['may_read'])]

    def resolve_issuer(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            issuer = Issuer.objects.get(id=id)
            if issuer.has_permissions(info.context.user, ['may_read']):
                return issuer

    def resolve_badge_classes(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.all() if bc.has_permissions(info.context.user, ['may_read'])]

    def resolve_badge_class(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeClass.objects.get(id=id)
            if bc.has_permissions(info.context.user, ['may_read']):
                return bc

    def resolve_badge_instances(self, info, **kwargs):
        return list(info.context.user.cached_badgeinstances())
