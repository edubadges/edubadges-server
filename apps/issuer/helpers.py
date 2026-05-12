# encoding: utf-8


import uuid
from collections import MutableMapping

from django.core.cache import cache
from requests_cache.backends import BaseCache


class DjangoCacheDict(MutableMapping):
    _keymap_cache_key = "DjangoCacheDict_keys"

    def __init__(self, namespace, id=None, timeout=None):
        self.namespace = namespace
        self._timeout = timeout

        if id is None:
            id = uuid.uuid4().hexdigest()
        self._id = id
        self.keymap_cache_key = self._keymap_cache_key+"_"+self._id

    def build_key(self, *args):
        return "{keymap_cache_key}{namespace}{key}".format(
            keymap_cache_key=self.keymap_cache_key,
            namespace=self.namespace,
            key="".join(args)
        ).encode("utf-8")

    def timeout(self):
        return self._timeout

    def _keymap(self):
        keymap = cache.get(self.keymap_cache_key)
        if keymap is None:
            return []
        return keymap

    def __getitem__(self, key):
        result = cache.get(self.build_key(key))
        if result is None:
            raise KeyError
        return result

    def __setitem__(self, key, value):
        built_key = self.build_key(key)
        cache.set(built_key, value, timeout=self.timeout())

        # this probably needs locking...
        keymap = self._keymap()
        keymap.append(built_key)
        cache.set(self.keymap_cache_key, keymap, timeout=None)

    def __delitem__(self, key):
        built_key = self.build_key(key)
        cache.delete(built_key)

        # this probably needs locking...
        keymap = self._keymap()
        keymap.remove(built_key)
        cache.set(self.keymap_cache_key, keymap, timeout=None)

    def __len__(self):
        keymap = self._keymap()
        return len(keymap)

    def __iter__(self):
        keymap = self._keymap()
        for key in keymap:
            yield cache.get(key)

    def __str__(self):
        return '<{}>'.format(self.keymap_cache_key)

    def clear(self):
        self._id = uuid.uuid4().hexdigest()
        self.keymap_cache_key = self._keymap_cache_key+"_"+self._id


class DjangoCacheRequestsCacheBackend(BaseCache):
    def __init__(self, namespace='requests-cache', **options):
        super(DjangoCacheRequestsCacheBackend, self).__init__(**options)
        self.responses = DjangoCacheDict(namespace, 'responses')
        self.keys_map = DjangoCacheDict(namespace, 'urls')
