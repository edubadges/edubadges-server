from django.db import models
from django.conf import settings
import cachemodel

from badgeanalysis.models import OpenBadge


class ConsumerBadge(cachemodel.CacheModel):
    consumer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True)
    badge = models.OneToOneField(OpenBadge, related_name='consumerbadge', null=True, blank=False)

    def __unicode__(self):
        return str(self.badge)

    @property
    def owner(self):
        return self.consumer
