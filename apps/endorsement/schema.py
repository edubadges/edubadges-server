import graphene
from graphene_django.types import DjangoObjectType

from endorsement.models import Endorsement


class EndorsementType(DjangoObjectType):
    class Meta:
        model = Endorsement
        fields = (
            'entity_id', 'endorser', 'endorsee', 'claim', 'description', 'status', 'revocation_reason',
            'rejection_reason', 'created_at', 'updated_at')


class Query(object):
    endorsements = graphene.List(EndorsementType)

    def resolve_endorsements(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return Endorsement.objects.filter(badge_class__entity_id=id)
