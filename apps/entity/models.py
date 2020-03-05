# encoding: utf-8
import cachemodel
from django.db import models

from mainsite.utils import generate_entity_uri


class _AbstractVersionedEntity(cachemodel.CacheModel):

    class Meta:
        abstract = True

    def get_entity_class_name(self):
        if hasattr(self, 'entity_class_name') and self.entity_class_name:
            return self.entity_class_name
        return self.__class__.__name__

    def save(self, *args, **kwargs):
        if self.entity_id is None:
            self.entity_id = generate_entity_uri()

        return super(_AbstractVersionedEntity, self).save(*args, **kwargs)

    def publish(self):
        super(_AbstractVersionedEntity, self).publish()
        self.publish_by('entity_id')

    def delete(self, *args, **kwargs):
        self.publish_delete('entity_id')
        return super(_AbstractVersionedEntity, self).delete(*args, **kwargs)


class BaseVersionedEntity(_AbstractVersionedEntity):
    entity_id = models.CharField(max_length=254, unique=True, default=None)  # default=None is required

    class Meta:
        abstract = True

    def __unicode__(self):
        try:
            return '{}{}'.format(type(self)._meta.object_name, self.entity_id)
        except AttributeError:
            return self.entity_id

