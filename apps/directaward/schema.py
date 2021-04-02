import graphene
from graphene_django.types import DjangoObjectType


from directaward.models import DirectAward, DirectAwardBundle


class DirectAwardType(DjangoObjectType):

    class Meta:
        model = DirectAward
        fields = ('entity_id', 'eppn', 'status', 'recipient_email', 'badgeclass', 'created_at', 'updated_at')


class DirectAwardBundleType(DjangoObjectType):

    class Meta:
        model = DirectAwardBundle
        fields = ('entity_id', 'badgeclass', 'created_at', 'updated_at',
                  'assertion_count', 'direct_award_count', 'initial_total')

    assertion_count = graphene.Int()
    direct_award_count = graphene.Int()
    direct_awards = graphene.List(DirectAwardType)

    def resolve_direct_awards(self, info, **kwargs):
        return self.cached_direct_awards()


class Query(object):
    direct_awards = graphene.List(DirectAwardType)
    direct_award = graphene.Field(DirectAwardType, id=graphene.String())

    def resolve_direct_awards(self, info, **kwargs):
        return list(info.context.user.direct_awards)

    def resolve_direct_award(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            da = DirectAward.objects.get(entity_id=id)
            if da.eppn in info.context.user.eppns:
                return da
