import graphene
from graphene_django.types import DjangoObjectType
from .models import Issuer, BadgeClass
from mainsite.mixins import StaffResolverMixin
from staff.schema import IssuerStaffType, BadgeClassStaffType

class ImageResolverMixin(object):

    def resolve_image(self, info):
        return self.image_url()


class IssuerType(StaffResolverMixin, ImageResolverMixin, DjangoObjectType):

    class Meta:
        model = Issuer
        fields = ('name', 'entity_id', 'badgeclasses', 'faculty',
                  'image', 'description', 'url', 'email', 'staff')

    staff = graphene.List(IssuerStaffType)

    badgeclasses_count = graphene.Int()

    def resolve_badgeclasses(self, info):
        return self.get_badgeclasses(info.context.user, ['read'])

    def resolve_badgeclasses_count(self, info):
        return len(self.get_badgeclasses(info.context.user, ['read']))


class BadgeClassType(StaffResolverMixin, ImageResolverMixin, DjangoObjectType):

    class Meta:
        model = BadgeClass
        fields = ('name', 'entity_id', 'issuer', 'image', 'staff',
                  'description', 'criteria_url', 'criteria_text',)

    staff = graphene.List(BadgeClassStaffType)


class Query(object):
    issuers = graphene.List(IssuerType)
    badge_classes = graphene.List(BadgeClassType)
    issuer = graphene.Field(IssuerType, id=graphene.ID())
    badge_class = graphene.Field(BadgeClassType, id=graphene.ID())

    def resolve_issuers(self, info, **kwargs):
        return [issuer for issuer in Issuer.objects.all() if issuer.has_permissions(info.context.user, ['read'])]

    def resolve_issuer(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            issuer = Issuer.objects.get(id=id)
            if issuer.has_permissions(info.context.user, ['read']):
                return issuer

    def resolve_badge_classes(self, info, **kwargs):
        return [bc for bc in BadgeClass.objects.all() if bc.has_permissions(info.context.user, ['read'])]

    def resolve_badge_class(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            bc = BadgeClass.objects.get(id=id)
            if bc.has_permissions(info.context.user, ['read']):
                return bc
