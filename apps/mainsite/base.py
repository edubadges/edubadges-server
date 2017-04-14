# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
from django.db import models

from mainsite.utils import generate_entity_uri


class BaseVersionedEntity(cachemodel.CacheModel):
    entity_id = models.CharField(max_length=254, blank=False, null=True, default=None)
    entity_version = models.PositiveIntegerField(blank=False, null=False, default=1)

    class Meta:
        abstract = True

    def get_entity_class_name(self):
        if self.entity_class_name:
            return self.entity_class_name
        return self.__class__.__name__

    def save(self, *args, **kwargs):
        if self.entity_id is None:
            self.entity_id = generate_entity_uri(self.get_entity_class_name())

        self.entity_version += 1
        return super(BaseVersionedEntity, self).save(*args, **kwargs)

    def publish(self):
        super(BaseVersionedEntity, self).publish()
        self.publish_by('entity_id')

    def delete(self, *args, **kwargs):
        return super(BaseVersionedEntity, self).delete(*args, **kwargs)
        self.publish_delete('entity_id')

