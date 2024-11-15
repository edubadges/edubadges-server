import graphene
from graphene_django.types import DjangoObjectType

from directaward.models import DirectAward, DirectAwardBundle


class DirectAwardType(DjangoObjectType):
    class Meta:
        model = DirectAward
        fields = ('entity_id', 'eppn', 'status', 'recipient_email', 'badgeclass', 'created_at', 'updated_at',
                  'resend_at', 'delete_at')


class DirectAwardBundleType(DjangoObjectType):
    class Meta:
        model = DirectAwardBundle
        fields = ('entity_id', 'badgeclass', 'created_at', 'updated_at', 'identifier_type',
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
    all_unclaimed_direct_awards = graphene.List(DirectAwardType)
    all_deleted_direct_awards = graphene.List(DirectAwardType)
    deleted_direct_awards = graphene.List(DirectAwardType)
    direct_award = graphene.Field(DirectAwardType, id=graphene.String())

    def resolve_direct_awards(self, info, **kwargs):
        return list(info.context.user.direct_awards)

    def resolve_direct_award(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            da = DirectAward.objects.get(entity_id=id)
            user = info.context.user
            if da.eppn in user.eppns or (da.recipient_email == user.email and da.bundle.identifier_type == DirectAwardBundle.IDENTIFIER_EMAIL):
                return da

    def resolve_all_unclaimed_direct_awards(self, info, **kwargs):
        user = info.context.user
        return [da for da in DirectAward.objects.filter(badgeclass__issuer__faculty__institution=user.institution,
                                                        status__in=[DirectAward.STATUS_UNACCEPTED,
                                                                    DirectAward.STATUS_SCHEDULED]) if
                da.badgeclass.has_permissions(info.context.user, ['may_award'])]

    def resolve_all_deleted_direct_awards(self, info, **kwargs):
        user = info.context.user
        return [da for da in DirectAward.objects.filter(badgeclass__issuer__faculty__institution=user.institution,
                                                        status=DirectAward.STATUS_DELETED) if
                da.badgeclass.has_permissions(info.context.user, ['may_award'])]
