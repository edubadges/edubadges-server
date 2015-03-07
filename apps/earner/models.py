from django.db import models
from django.conf import settings
import cachemodel

from badgeanalysis.models import OpenBadge


class EarnerBadge(cachemodel.CacheModel):
    earner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    badge = models.OneToOneField(OpenBadge, related_name='earnerbadge', null=True, blank=False)
    earner_description = models.TextField(blank=True)
    earner_accepted = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.badge)

    @property
    def owner(self):
        return self.earner
