from django.conf import settings
from django.db import models

from mainsite.models import (AbstractIssuer, AbstractBadgeClass,
                             AbstractBadgeInstance)


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Issuer(AbstractIssuer):
    pass


class BadgeClass(AbstractBadgeClass):
    issuer = models.ForeignKey(Issuer, blank=False, null=False,
                               on_delete=models.PROTECT,
                               related_name="badgeclasses")


class BadgeInstance(AbstractBadgeInstance):
    # 0.5 BadgeInstances have no notion of a BadgeClass
    badgeclass = models.ForeignKey(BadgeClass, blank=False, null=True,
                                   on_delete=models.PROTECT,
                                   related_name='badgeinstances')
    # 0.5 BadgeInstances have no notion of a BadgeClass
    issuer = models.ForeignKey(Issuer, blank=False, null=True)
