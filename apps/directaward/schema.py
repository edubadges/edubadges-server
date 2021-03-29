from graphene_django.types import DjangoObjectType
from directaward.models import DirectAward


class DirectAwardType(DjangoObjectType):

    class Meta:
        model = DirectAward
        fields = ('entity_id', 'eppn', 'recipient_email', 'badgeclass', 'created_at', 'updated_at')
