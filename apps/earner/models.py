from django.db import models
from django.conf import settings
import basic_models
import cachemodel
from django.contrib.auth import get_user_model

from badgeanalysis.models import OpenBadge



class EarnerBadge(cachemodel.CacheModel):
    earner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    badge = models.ForeignKey(OpenBadge, null=False)
    earner_description = models.TextField(blank=True)
    earner_accepted = models.BooleanField(default=False)

    def __unicode__(self):
        return str(self.badge)

# class EarnerRegisteredEmail(basic_models.ActiveModel):
#     email = models.CharField(max_length=254)
#     confirmed = models.BooleanField(default=False)