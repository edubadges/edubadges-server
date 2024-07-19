import graphene
from graphene_django.types import DjangoObjectType
from datetime import datetime
import badgeuser.schema
import directaward.schema
import institution.schema
import issuer.schema
import lti13.schema
import lti_edu.schema
import notifications.schema
from mainsite.models import SystemNotification


class SystemNotificationType(DjangoObjectType):
    class Meta:
        model = SystemNotification
        fields = ('title', 'notification_en','notification_nl', 'display_start', 'display_end', 'notification_type')


class Query(institution.schema.Query,
            badgeuser.schema.Query,
            issuer.schema.Query,
            lti13.schema.Query,
            lti_edu.schema.Query,
            directaward.schema.Query,
            notifications.schema.Query,
            graphene.ObjectType):
    system_notifications = graphene.List(SystemNotificationType)

    def resolve_system_notifications(self, info, **kwargs):
        today = datetime.utcnow()
        valid_notifications = SystemNotification.objects \
            .filter(display_start__lt=today) \
            .filter(display_end__gte=today) \
            .all()
        return valid_notifications


schema = graphene.Schema(query=Query)
