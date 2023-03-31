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
                  'assertion_count', 'direct_award_count', 'direct_award_rejected_count',
                  'direct_award_scheduled_count', 'direct_award_revoked_count', 'initial_total')

    assertion_count = graphene.Int()
    direct_award_count = graphene.Int()
    direct_award_rejected_count = graphene.Int()
    direct_award_scheduled_count = graphene.Int()
    direct_award_revoked_count = graphene.Int()
    direct_awards = graphene.List(DirectAwardType)

    def resolve_direct_awards(self, info, **kwargs):
        return self.cached_direct_awards()


class Query(object):
    direct_awards = graphene.List(DirectAwardType)
    all_direct_awards = graphene.List(DirectAwardType)
    direct_award = graphene.Field(DirectAwardType, id=graphene.String())

    def resolve_direct_awards(self, info, **kwargs):
        return list(info.context.user.direct_awards)

    def resolve_direct_award(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            da = DirectAward.objects.get(entity_id=id)
            if da.eppn in info.context.user.eppns:
                return da

    def resolve_all_direct_awards(self, info, **kwargs):
        user = info.context.user
        return [da for da in DirectAward.objects.filter(badgeclass__issuer__faculty__institution=user.institution,
                                                        status=DirectAward.STATUS_UNACCEPTED) if
                da.badgeclass.has_permissions(info.context.user, ['may_award'])]
