from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse

from autoslug import AutoSlugField
import cachemodel

from mainsite.models import (AbstractIssuer, AbstractBadgeClass,
                             AbstractBadgeInstance)

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class LocalIssuer(AbstractIssuer):
    pass


class LocalBadgeClass(AbstractBadgeClass):
    issuer = models.ForeignKey(LocalIssuer, blank=False, null=False,
                               on_delete=models.PROTECT,
                               related_name="badgeclasses")


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
            return default_storage.url(self.image)
        else:
            return getattr(settings, 'HTTP_ORIGIN') + default_storage.url(self.image)


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

    @property
    def share_url(self):
        if self.share_hash != '':
            return getattr(settings, 'HTTP_ORIGIN') + reverse(
                'shared_collection', args=[self.pk, self.share_hash])
        return ''


class LocalBadgeInstanceCollection(models.Model):
    instance = models.ForeignKey(LocalBadgeInstance, null=False)
    collection = models.ForeignKey(Collection, null=False)

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
