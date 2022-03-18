import graphene
from graphene_django.types import DjangoObjectType

from notifications.models import BadgeClassUserNotification


class BadgeClassUserNotificationType(DjangoObjectType):
    class Meta:
        model = BadgeClassUserNotification
        fields = ('badgeclass',)


class Query(object):
    notifications = graphene.List(BadgeClassUserNotificationType)

    def resolve_notifications(self, info, **kwargs):
        current_user = info.context.user
        results = BadgeClassUserNotification.objects.filter(user=current_user)
        return results
