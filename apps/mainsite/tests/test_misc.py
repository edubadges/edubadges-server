import re
import urllib
import urlparse
import warnings
import unittest
import os
from allauth.account.models import EmailConfirmation
from django.core import mail
from django.core.cache import cache, CacheKeyWarning
from django.core.management import call_command
from django.test import override_settings, TransactionTestCase

from badgeuser.models import BadgeUser, CachedEmailAddress
from mainsite.models import BadgrApp
from mainsite import TOP_DIR
from mainsite.tests.base import BadgrTestCase


class TestCacheSettings(TransactionTestCase):

    @unittest.skip('For debug speedup')
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


@override_settings(
    HTTP_ORIGIN='http://api.testserver',
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=True
)
class TestSignup(BadgrTestCase):
    def test_user_signup_email_confirmation_redirect(self):
        from django.conf import settings
        http_origin = getattr(settings, 'HTTP_ORIGIN')
        badgr_app = BadgrApp(cors='frontend.ui',
                             email_confirmation_redirect='http://frontend.ui/login/',
                             forgot_password_redirect='http://frontend.ui/forgot-password/')
        badgr_app.save()

        with self.settings(BADGR_APP_ID=badgr_app.id):
            post_data = {
                'first_name': 'Tester',
                'last_name': 'McSteve',
                'email': 'test12345@example.com',
                'password': 'secr3t4nds3cur3'
            }
            response = self.client.post('/v1/user/profile', post_data)
            self.assertEqual(response.status_code, 201)

            user = BadgeUser.objects.get(entity_id=response.data.get('slug'))

            self.assertEqual(len(mail.outbox), 1)
            url_match = re.search(r'{}(/v1/user/confirmemail.*)'.format(http_origin), mail.outbox[0].body)
            self.assertIsNotNone(url_match)
            confirm_url = url_match.group(1)

            expected_redirect_url = '{badgrapp_redirect}{first_name}?authToken={auth}&email={email}'.format(
                badgrapp_redirect=badgr_app.email_confirmation_redirect,
                first_name=post_data['first_name'],
                email=urllib.quote(post_data['email']),
                auth=user.auth_token
            )

            response = self.client.get(confirm_url, follow=False)
            self.assertEqual(response.status_code, 302)

            actual = urlparse.urlparse(response.get('location'))
            expected = urlparse.urlparse(expected_redirect_url)
            self.assertEqual(actual.netloc, expected.netloc)
            self.assertEqual(actual.scheme, expected.scheme)

            actual_query = urlparse.parse_qs(actual.query)
            expected_query = urlparse.parse_qs(expected.query)
            self.assertEqual(actual_query.get('email'), expected_query.get('email'))
            self.assertIsNotNone(actual_query.get('authToken'))

@override_settings(
    ACCOUNT_EMAIL_CONFIRMATION_HMAC=False
)
class TestEmailCleanupCommand(BadgrTestCase):

    @unittest.skip('For debug speedup')
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

    @unittest.skip('For debug speedup')
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
