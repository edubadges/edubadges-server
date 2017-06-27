# encoding: utf-8
from __future__ import unicode_literals

import os

import basic_models
import cachemodel
from django.core.urlresolvers import reverse
from django.db import models, transaction

from entity.models import BaseVersionedEntity
from issuer.models import BaseAuditedModel, BadgeInstance
from backpack.sharing import SharingManager
from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.utils import OriginSetting


class BackpackCollection(BaseAuditedModel, BaseVersionedEntity):
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    share_hash = models.CharField(max_length=255, null=False, blank=True)

    # slug has been deprecated, but keep for legacy collections redirects
    slug = models.CharField(max_length=254, blank=True, null=True, default=None)

    assertions = models.ManyToManyField('issuer.BadgeInstance', blank=True, through='backpack.BackpackCollectionBadgeInstance')

    cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='entity_id', slug_field_name='entity_id')

    def publish(self):
        super(BackpackCollection, self).publish()
        self.created_by.publish()

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return self.assertions.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_collects(self):
        return self.backpackcollectionbadgeinstance_set.all()

    @property
    def owner(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(id=self.created_by_id)

    # Convenience methods for toggling published state
    @property
    def published(self):
        return bool(self.share_hash)

    @published.setter
    def published(self, value):
        if value and not self.share_hash:
            self.share_hash = os.urandom(16).encode('hex')
        elif not value and self.share_hash:
            self.share_hash = ''

    @property
    def share_url(self):
        if self.published:
            return OriginSetting.HTTP+reverse('backpack_shared_collection', kwargs={'share_hash': self.share_hash})

    @property
    def badge_items(self):
        return self.cached_badgeinstances()

    @badge_items.setter
    def badge_items(self, value):
        """
        Update this collection's list of BackpackCollectionBadgeInstance from a list of BadgeInstance EntityRelatedFieldV2 serializer data
        """
        with transaction.atomic():
            existing_badges = {b.entity_id: b for b in self.badge_items}
            # add missing badges
            for badge_entity_id in value:
                try:
                    badgeinstance = BadgeInstance.cached.get(entity_id=badge_entity_id)
                except BadgeInstance.DoesNotExist:
                    pass
                else:
                    if badge_entity_id not in existing_badges.keys():
                        BackpackCollectionBadgeInstance.cached.get_or_create(
                            collection=self,
                            badgeinstance=badgeinstance
                        )

            # remove badges no longer in collection
            for badge_entity_id, badgeinstance in existing_badges.items():
                if badge_entity_id not in value:
                    BackpackCollectionBadgeInstance.objects.filter(
                        collection=self,
                        badgeinstance=badgeinstance
                    ).delete()


class BackpackCollectionBadgeInstance(cachemodel.CacheModel):
    collection = models.ForeignKey('backpack.BackpackCollection')
    badgeinstance = models.ForeignKey('issuer.BadgeInstance')

    def publish(self):
        super(BackpackCollectionBadgeInstance, self).publish()
        self.collection.publish()

    def delete(self):
        super(BackpackCollectionBadgeInstance, self).delete()
        self.collection.publish()

    @property
    def cached_badgeinstance(self):
        return BadgeInstance.cached.get(id=self.badgeinstance_id)

    @property
    def cached_collection(self):
        return BackpackCollection.cached.get(id=self.collection_id)


class BaseSharedModel(cachemodel.CacheModel, basic_models.TimestampedModel):
    SHARE_PROVIDERS = [(p.provider_code, p.provider_name) for code,p in SharingManager.ManagerProviders.items()]
    provider = models.CharField(max_length=254, choices=SHARE_PROVIDERS)

    class Meta:
        abstract = True

    def get_share_url(self, provider, **kwargs):
        raise NotImplementedError()


class BackpackBadgeShare(BaseSharedModel):
    badgeinstance = models.ForeignKey("issuer.BadgeInstance", null=True)

    def get_share_url(self, provider, **kwargs):
        return SharingManager.share_url(provider, self.badge, **kwargs)


class BackpackCollectionShare(BaseSharedModel):
    collection = models.ForeignKey('backpack.BackpackCollection', null=False)

    def get_share_url(self, provider, **kwargs):
        return SharingManager.share_url(provider, self.collection, **kwargs)
