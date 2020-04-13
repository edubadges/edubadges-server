import graphene
from graphene_django import DjangoObjectType

import institution.schema
import badgeuser.models


class BadgeUserType(DjangoObjectType):
    class Meta:
        model = badgeuser.models.BadgeUser
        fields = ('first_name', 'last_name', 'email', 'entity_id')

    institution = graphene.Field(institution.schema.InstitutionType)


class Query(object):
    current_user = graphene.Field(BadgeUserType)

    def resolve_current_user(self, info, **kwargs):
        return info.context.user
