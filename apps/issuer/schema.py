import graphene
from graphene_django.types import DjangoObjectType
from .models import Issuer, BadgeClass


class IssuerType(DjangoObjectType):

    class Meta:
        model = Issuer
        exclude = ('id',)

    def resolve_badgeclasses(self, info):
        return self.get_badgeclasses(info.context.user, ['read'])


class BadgeClassType(DjangoObjectType):

    class Meta:
        model = BadgeClass
        exclude = ('id',)

    def resolve_image(self, info):
        return self.image_url()


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
        id =  kwargs.get('id')
        if id is not None:
            bc = BadgeClass.objects.get(id=id)
            if bc.has_permissions(info.context.user, ['read']):
                return bc
