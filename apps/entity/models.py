# encoding: utf-8
import cachemodel
from cachemodel.utils import generate_cache_key
from django.db import models
from django.core.cache import cache

from mainsite.utils import generate_entity_uri


class BadgrCacheModel(cachemodel.CacheModel):

    class Meta:
        abstract = True

    def publish_delete_methods(self, method_names):
        """
        Deletes the cached values for the given method names
        """
        for method_name  in method_names:
            method = getattr(self, method_name, None)
            if not getattr(method, '_cached_method', False):
                raise AttributeError("method '%s' is not a cached_method.");
            target = getattr(method, '_cached_method_target', None)
            if callable(target):
                key = generate_cache_key([self.__class__.__name__, target.__name__, self.pk])
                cache.delete(key)


class _AbstractVersionedEntity(BadgrCacheModel):

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
