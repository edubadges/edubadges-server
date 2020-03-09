from graphene_django.types import DjangoObjectType
from badgeuser.models import BadgeUser


class BadgeUserType(DjangoObjectType):

    class Meta:
        model = BadgeUser
        fields = ('first_name', 'last_name', 'email', 'entity_id',)

