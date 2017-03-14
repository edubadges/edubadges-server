import os
import re
import time
import urllib
import warnings

from django.core import mail
from django.core.cache import cache, CacheKeyWarning
from django.core.cache.backends.filebased import FileBasedCache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils.six import StringIO

from allauth.account.models import EmailConfirmation
from rest_framework.test import APITestCase

from mainsite.models import BadgrApp
from mainsite.settings import TOP_DIR

from badgeuser.models import BadgeUser, CachedEmailAddress


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


@override_settings(HTTP_ORIGIN='http://testserver')
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
        url_match = re.search(r'http://testserver(/v1/user/confirmemail.*)', mail.outbox[0].body)
        self.assertIsNotNone(url_match)
        confirm_url = url_match.group(1)

        confirmation = EmailConfirmation.objects.first()

        with self.settings(ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL='http://frontend.ui/login/',
                           BADGR_APP_ID=badgr_app.id):
            response = self.client.get(confirm_url, follow=False)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.get('location'), 'http://testserver/login/Tester?email={}'.format(urllib.quote(post_data['email'])))


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    },
)
class CachingTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        test_cache = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        test_cache.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))


class TestEmailCleanupCommand(TestCase):
    def test_email_added_for_user_missing_one(self):
        user = BadgeUser(email="newtest@example.com", first_name="Test", last_name="User")
        user.save()
        self.assertFalse(CachedEmailAddress.objects.filter(user=user).exists())

        user2 = BadgeUser(email="newtest2@example.com", first_name="Test2", last_name="User")
        user2.save()
        email2 = CachedEmailAddress(user=user2, email="newtest2@example.com", verified=False, primary=True)
        email2.save()

        call_command('clean_email_records')

        email_record = CachedEmailAddress.objects.get(user=user)
        self.assertFalse(email_record.verified)
        self.assertTrue(email_record.emailconfirmation_set.exists())
        self.assertEqual(len(mail.outbox), 1)

    def test_unverified_unprimary_email_sends_confirmation(self):
        """
        If there is only one email, and it's not primary, set it as primary.
        If it's not verified, send a verification.
        """
        user = BadgeUser(email="newtest@example.com", first_name="Test", last_name="User")
        user.save()
        email = CachedEmailAddress(email=user.email, user=user, verified=False, primary=False)
        email.save()

        user2 = BadgeUser(email="newtest@example.com", first_name="Error", last_name="User")
        user2.save()

        self.assertEqual(BadgeUser.objects.count(), 2)

        call_command('clean_email_records')

        email_record = CachedEmailAddress.objects.get(user=user)
        self.assertTrue(email_record.primary)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(BadgeUser.objects.count(), 1)
