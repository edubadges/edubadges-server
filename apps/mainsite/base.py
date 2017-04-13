# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
from django.db import models

from mainsite.utils import generate_entity_uri


class BaseEntity(cachemodel.CacheModel):
    entity_id = models.CharField(max_length=254, blank=False, null=True, default=None)
    entity_version = models.PositiveIntegerField(blank=False, null=False, default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.entity_id is None:
            self.entity_id = generate_entity_uri(self.__class__.__name__)

        self.entity_version += 1
        return super(BaseEntity, self).save(*args, **kwargs)

    def publish(self):
        super(BaseEntity, self).publish()
        self.publish_by('entityId')

    def delete(self, *args, **kwargs):
        return super(BaseEntity, self).delete(*args, **kwargs)
        self.publish_delete('entityId')

