from django.core.cache import cache
from django.db import models
from cachemodel import CACHE_FOREVER_TIMEOUT
from cachemodel.utils import generate_cache_key


class CacheModelManager(models.Manager):
    def get(self, **kwargs):
        key = generate_cache_key([self.model.__name__, "get"], **kwargs)
        obj = cache.get(key)
        if obj is None:
            obj = super(CacheModelManager, self).get(**kwargs)
            cache.set(key, obj, CACHE_FOREVER_TIMEOUT)

            # update cache_key_index with obj.pk <- key
        return obj

    def get_or_create(self, **kwargs):
        key = generate_cache_key([self.model.__name__, "get"], **kwargs)
        obj = cache.get(key)
        if obj is None:
            return super(CacheModelManager, self).get_or_create(**kwargs)
        else:
            return obj, False

    def get_by(self, *args, **kwargs):
        raise DeprecationWarning("get_by() has been deprecated, use .get() instead.")
        raise NotImplementedError

class CachedTableManager(models.Manager):
    def _pk_field_name(self):
        for field in self.model._meta.fields:
            if field.primary_key:
                return field.name

    def _rebuild_indices(self):
        for field in self.model._meta.fields:
            if field.primary_key or field.db_index:
                self._rebuild_index(field.name)

    def _rebuild_index(self, field_name):
        cache_key = generate_cache_key([self.model.__name__, "table"], field_name)
        table = {}
        for obj in super(CachedTableManager, self).all().select_related():
            key = getattr(obj, field_name, None)
            if key is not None:
                table[key] = obj
        cache.set(cache_key, table, CACHE_FOREVER_TIMEOUT);
        return table

    def _fetch_index(self, field_name):
        cache_key = generate_cache_key([self.model.__name__, "table"], field_name)
        table = cache.get(cache_key)
        if table is None:
            table = self._rebuild_index(field_name)
        return table

    def get(self, **kwargs):
        if len(list(kwargs.keys())) > 1:
            raise NotImplementedError("Multiple indices are not supported on CachedTable.")

        field, value = list(kwargs.items())[0]
        if field == 'pk':
            field = self._pk_field_name()
        table = self._fetch_index(field)
        if value not in table:
            raise self.model.DoesNotExist
        return table[value]

    def all(self):
        table = self._fetch_index(self._pk_field_name())
        return list(table.values())
