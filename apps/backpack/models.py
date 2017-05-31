# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
from django.db import models

from entity.models import BaseVersionedEntity
from issuer.models import BaseAuditedModel


class BackpackCollection(BaseAuditedModel, BaseVersionedEntity):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    share_hash = models.CharField(max_length=255, null=False, blank=True)

    # slug has been deprecated, but keep for legacy collections redirects
    slug = models.CharField(max_length=254, blank=True, null=True, default=None)

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return self.collectionbadgeinstance_set.all()


class BackpackCollectionBadgeInstance(cachemodel.CacheModel):
    collection = models.ForeignKey('backpack.BackpackCollection')
    badgeinstance = models.ForeignKey('issuer.BadgeInstance')

    def publish(self):
        super(BackpackCollectionBadgeInstance, self).publish()
        self.collection.publish()

    def delete(self):
        super(BackpackCollectionBadgeInstance, self).delete()
        self.collection.publish()

