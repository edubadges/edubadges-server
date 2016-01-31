import os
import warnings

from django.core.cache import cache, CacheKeyWarning
from django.test import TestCase, override_settings

from mainsite.settings import TOP_DIR


class TestCacheSettings(TestCase):

    def test_long_cache_keys_shortened(self):
        cache_settings = {
            'default': {
                'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
                'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
            }
        }
        long_key_string = "X" * 251

        with override_settings(CACHES=cache_settings):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                # memcached limits key length to 250
                cache.set(long_key_string, "hello cached world")

                self.assertEqual(len(w), 1)
                self.assertIsInstance(w[0].message, CacheKeyWarning)

        # Activate optional cache key length checker
        cache_settings['default']['KEY_FUNCTION'] = 'mainsite.utils.filter_cache_key'

        with override_settings(CACHES=cache_settings):
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                # memcached limits key length to 250
                cache.set(long_key_string, "hello cached world")

                self.assertEqual(len(w), 0)

                retrieved = cache.get(long_key_string)

                self.assertEqual(retrieved, "hello cached world")
