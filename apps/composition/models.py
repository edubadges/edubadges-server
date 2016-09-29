import os

import cachemodel
from autoslug import AutoSlugField
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import models

from mainsite.models import (AbstractIssuer, AbstractBadgeClass,
                             AbstractBadgeInstance, AbstractRemoteImagePreviewMixin)

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class LocalIssuer(AbstractRemoteImagePreviewMixin, AbstractIssuer):
    pass


class LocalBadgeClass(AbstractRemoteImagePreviewMixin, AbstractBadgeClass):
    issuer = models.ForeignKey(LocalIssuer, blank=False, null=False,
                               on_delete=models.PROTECT,
                               related_name="badgeclasses")

    class Meta:
        verbose_name = 'local badge class'
        verbose_name_plural = 'local badge classes'


class LocalBadgeInstance(AbstractBadgeInstance):
    # 0.5 BadgeInstances have no notion of a BadgeClass
    badgeclass = models.ForeignKey(LocalBadgeClass, blank=False, null=True,
                                   on_delete=models.PROTECT,
                                   related_name='badgeinstances')
    # 0.5 BadgeInstances have no notion of a BadgeClass
    issuer = models.ForeignKey(LocalIssuer, blank=False, null=True)

    recipient_user = models.ForeignKey(AUTH_USER_MODEL)

    def image_url(self):
        if getattr(settings, 'MEDIA_URL').startswith('http'):
            return default_storage.url(self.image.name)
        else:
            return getattr(settings, 'HTTP_ORIGIN') + default_storage.url(self.image.name)


class Collection(cachemodel.CacheModel):
    name = models.CharField(max_length=128)
    slug = AutoSlugField(max_length=128, populate_from='name', blank=False,
                         editable=True)
    description = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)
    share_hash = models.CharField(max_length=255, null=False, blank=True)

    instances = models.ManyToManyField(LocalBadgeInstance,
                                       through='LocalBadgeInstanceCollection')
    shared_with = models.ManyToManyField(AUTH_USER_MODEL,
                                         through='CollectionPermission',
                                         related_name='shared_with_me')

    class Meta:
        unique_together = ('owner', 'slug')

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
        if self.share_hash != '':
            return getattr(settings, 'HTTP_ORIGIN') + reverse(
                'shared_collection', args=[self.pk, self.share_hash])
        return ''


class LocalBadgeInstanceCollection(models.Model):
    instance = models.ForeignKey(LocalBadgeInstance, null=False)
    collection = models.ForeignKey(Collection, null=False, related_name='badges')

    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('instance', 'collection')
        verbose_name = "BadgeInstance in a Collection"
        verbose_name_plural = "BadgeInstances in Collections"

    def __unicode__(self):
        return u'{} in {}\'s {}'.format(
            self.instance.badgeclass.name,
            self.instance.recipient_user.username,
            self.collection.name
        )


class CollectionPermission(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, null=False)
    collection = models.ForeignKey(Collection, null=False)

    can_write = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'collection')
