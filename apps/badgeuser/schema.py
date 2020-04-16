import graphene
from graphene_django.types import DjangoObjectType
from badgeuser.models import BadgeUser
from institution.schema import InstitutionType

class BadgeUserType(DjangoObjectType):

    class Meta:
        model = BadgeUser
        fields = ('first_name', 'last_name', 'email', 'entity_id')

    institution = graphene.Field(InstitutionType)


class Query(object):
    current_user = graphene.Field(BadgeUserType)

    def resolve_current_user(self, info, **kwargs):
        return info.context.user
