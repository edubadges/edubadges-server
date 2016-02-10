import os
import warnings

from django.core import mail
from django.core.cache import cache, CacheKeyWarning
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from allauth.account.models import EmailConfirmation
from rest_framework.test import APITestCase

from mainsite.models import BadgrApp
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


class TestSignup(APITestCase):
    def test_user_signup_email_confirmation_redirect(self):
        badgr_app = BadgrApp(cors='testserver',
                             email_confirmation_redirect='http://testserver/login/',
                             forgot_password_redirect='http://testserver/forgot-password/')
        badgr_app.save()

        post_data = {
            'first_name': 'Tester',
            'last_name': 'McSteve',
            'email': 'test12345@example.com',
            'password': '1234567'
        }
        self.client.post('/v1/user/profile', post_data)

        self.assertEqual(len(mail.outbox), 1)

        confirmation = EmailConfirmation.objects.first()

        with self.settings(ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL='http://frontend.ui/login/'):
            response = self.client.get(
                reverse('account_confirm_email', kwargs={ 'key': confirmation.key }),
                follow=False
            )
            self.assertRedirects(response, 'http://testserver/login/Tester', fetch_redirect_response=False)
