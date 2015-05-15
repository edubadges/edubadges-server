from django.db import models
from django.conf import settings

from autoslug import AutoSlugField
import cachemodel

from credential_store.models import StoredBadgeInstance

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class AbstractEarnerObject(cachemodel.CacheModel):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, null=False)

    class Meta:
        abstract = True

    @property
    def owner(self):
        return self.recipient


class Collection(AbstractEarnerObject):
    name = models.CharField(max_length=128)
    slug = AutoSlugField(
        max_length=128, populate_from='name',
        blank=False, editable=True
    )
    description = models.CharField(max_length=255, blank=True)

    instances = models.ManyToManyField(
        StoredBadgeInstance, through='StoredBadgeInstanceCollection'
    )
    viewers = models.ManyToManyField(
        AUTH_USER_MODEL, through='CollectionPermission', related_name='sharee'
    )

    class Meta:
        unique_together = (("recipient", "slug"),)


class StoredBadgeInstanceCollection(models.Model):
    instance = models.ForeignKey(StoredBadgeInstance, null=False)
    collection = models.ForeignKey(Collection, null=False)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('instance', 'collection')


class CollectionPermission(models.Model):
    collection = models.ForeignKey(Collection, null=False)
    viewer = models.ForeignKey(AUTH_USER_MODEL, null=False)
    writeable = models.BooleanField(default=False)

    class Meta:
        unique_together = ('collection', 'viewer')
