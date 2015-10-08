from django.db import models
from django.conf import settings
from django.core.urlresolvers import reverse

from autoslug import AutoSlugField
import cachemodel

from credential_store.models import StoredBadgeInstance

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')

######
#
# !!! This app and all its models have been deprecated !!!
# see the new 'composition' app
#
#####


class Collection(cachemodel.CacheModel):
    name = models.CharField(max_length=128)
    slug = AutoSlugField(
        max_length=128, populate_from='name',
        blank=False, editable=True
    )
    description = models.CharField(max_length=255, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, related_name="composer_collection_set")
    share_hash = models.CharField(max_length=255, null=False, blank=True)

    instances = models.ManyToManyField(
        StoredBadgeInstance, through='StoredBadgeInstanceCollection'
    )
    shared_with = models.ManyToManyField(
        AUTH_USER_MODEL, through='CollectionPermission', related_name='composer_shared_with_me'
    )

    class Meta:
        unique_together = ('owner', 'slug')

    @property
    def share_url(self):
        if self.share_hash != '':
            return getattr(settings, 'HTTP_ORIGIN') + reverse(
                'shared_collection',
                args=[self.pk, self.share_hash]
            )
        return ''


class StoredBadgeInstanceCollection(models.Model):
    instance = models.ForeignKey(StoredBadgeInstance, null=False)
    collection = models.ForeignKey(Collection, null=False)

    description = models.TextField(blank=True)

    class Meta:
        unique_together = ('instance', 'collection')


class CollectionPermission(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, null=False, related_name="composer_collectionpermission_set")
    collection = models.ForeignKey(Collection, null=False)

    can_write = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'collection')
