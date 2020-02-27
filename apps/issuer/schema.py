import graphene
from graphene_django.types import DjangoObjectType
from .models import Issuer, BadgeClass

class IssuerType(DjangoObjectType):
    class Meta:
        model = Issuer

class BadgeClassType(DjangoObjectType):
    class Meta:
        model = BadgeClass

class Query(object):
    issuers = graphene.List(IssuerType)
    def resolve_issuers(self, info, **kwargs):
        return Issuer.objects.all()

    issuer = graphene.Field(IssuerType, id=graphene.ID())
    def resolve_issuer(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Issuer.objects.get(id=id)

        return None

    badge_classes = graphene.List(BadgeClassType)
    def resolve_badge_classes(self, info, **kwargs):
        return BadgeClass.objects.all()

    badge_class = graphene.Field(BadgeClassType, id=graphene.ID())
    def resolve_badge_class(self, info, **kwargs):
        id =  kwargs.get('id')

        if id is not None:
            return BadgeClass.objects.get(id=id)

        return None