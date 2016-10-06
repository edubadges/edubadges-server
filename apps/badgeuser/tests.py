import os
import random
import re

import time
from django.contrib.auth import SESSION_KEY
from django.core.exceptions import ValidationError

from django.core import mail
from django.core.cache.backends.filebased import FileBasedCache
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.core.urlresolvers import reverse

from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase

from badgeuser.models import BadgeUser, CachedEmailAddress
from mainsite import TOP_DIR
from mainsite.models import BadgrApp

from badgeuser.models import EmailAddressVariant, CachedEmailAddress, ProxyEmailConfirmation

factory = APIRequestFactory()


class AuthTokenTests(APITestCase):
    fixtures = ['0001_initial_superuser']

    def test_create_user_auth_token(self):
        """
        Ensure that get can create a token for a user that doesn't have one
        and that it doesn't modify a token for a user that already has one.
        """
        self.client.force_authenticate(user=BadgeUser.objects.get(pk=1))
        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)
        token = response.data.get('token')
        self.assertRegexpMatches(token, r'[\da-f]{40}')

        second_response = self.client.get('/v1/user/auth-token')
        self.assertEqual(token, second_response.data.get('token'))

    def test_update_user_auth_token(self):
        """
        Ensure that a PUT request updates a user token.
        """
        user = BadgeUser.objects.get(pk=1)
        # Create a token for the first time.
        self.client.force_authenticate(user)
        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)
        token = response.data.get('token')
        self.assertRegexpMatches(token, r'[\da-f]{40}')

        # Ensure that token has changed.
        second_response = self.client.put('/v1/user/auth-token')
        self.assertNotEqual(token, second_response.data.get('token'))
        self.assertTrue(second_response.data.get('replace'))

        self.assertEqual(user.cached_token(), second_response.data.get('token'))
        self.assertEqual(Token.objects.get(user=user).key, user.cached_token())


class UserCreateTests(APITestCase):
    fixtures = ['0001_initial_superuser']

    def test_create_user(self):
        user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'newuniqueuser1@example.com',
            'password': '123456'
        }

        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    def test_create_user_with_already_claimed_email(self):
        user_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test2@example.com',
            'password': '123456'
        }

        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_can_create_user_with_preexisting_unconfirmed_email(self):
        user_data = {
            'first_name': 'NEW Test',
            'last_name': 'User',
            'email': 'unclaimed1@example.com',
            'password': '123456'
        }

        existing_email = CachedEmailAddress.objects.get(email="unclaimed1@example.com")
        existing_user = existing_email.user
        existing_user.save()
        self.assertFalse(existing_email.verified)
        self.assertTrue(existing_email in existing_user.cached_emails())

        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        new_user = BadgeUser.objects.get(first_name='NEW Test')
        self.assertEqual(new_user.email, 'unclaimed1@example.com')

        existing_email = CachedEmailAddress.objects.get(email="unclaimed1@example.com")
        self.assertEqual(existing_email.user, new_user)
        self.assertTrue(existing_email not in existing_user.cached_emails())


    def test_user_can_add_secondary_email_of_preexisting_unclaimed_email(self):
        first_user=BadgeUser.objects.get(pk=3)

        new_email = CachedEmailAddress(user=first_user, email="unclaimed2@example.com", primary=False, verified=False).save()

        second_user=BadgeUser.objects.get(pk=1)
        self.client.force_authenticate(user=second_user)
        response = self.client.post('/v1/user/emails', {
            'email': 'unclaimed2@example.com',
        })
        self.assertEqual(response.status_code, 201)


    def test_can_create_account_with_same_email_since_deleted(self):
        first_user_data = user_data = {
            'first_name': 'NEW Test',
            'last_name': 'User',
            'email': 'unclaimed1@example.com',
            'password': '123456'
        }
        response = self.client.post('/v1/user/profile', user_data)

        first_user = BadgeUser.objects.get(first_name='NEW Test')
        first_email = CachedEmailAddress.objects.get(email='unclaimed1@example.com')
        first_email.verified = True
        first_email.save()

        second_email = CachedEmailAddress(email='newjunkeremail@junk.net', user=first_user, verified=True)
        second_email.save()

        self.assertEqual(len(first_user.cached_emails()), 2)

        self.client.force_authenticate(user=first_user)
        response = self.client.put(
            reverse('api_user_email_detail', args=[second_email.pk]),
            {'primary': True}
        )
        self.assertEqual(response.status_code, 200)

        # Reload user and emails
        first_user = BadgeUser.objects.get(first_name='NEW Test')
        first_email = CachedEmailAddress.objects.get(email='unclaimed1@example.com')
        second_email = CachedEmailAddress.objects.get(email='newjunkeremail@junk.net')

        self.assertEqual(first_user.email, 'newjunkeremail@junk.net')
        self.assertTrue(second_email.primary)
        self.assertFalse(first_email.primary)

        self.assertTrue('unclaimed1@example.com' in [e.email for e in first_user.cached_emails()])
        first_email.delete()
        self.assertFalse('unclaimed1@example.com' in [e.email for e in first_user.cached_emails()])

        user_data['name'] = 'NEWEST Test'
        self.client.force_authenticate(user=None)
        response = self.client.post('/v1/user/profile', user_data)

        self.assertEqual(response.status_code, 201)

    def test_shouldnt_error_when_user_exists_with_email(self):
        email = 'existing3@example.test'

        old_user = BadgeUser(email=email, password='secret2')  # password is set because its an existing user
        old_user.save()
        old_user_email = CachedEmailAddress(email=email, user=old_user, verified=True)
        old_user_email.save()

        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secret',
            'email': email
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(mail.outbox), 0)

    def test_autocreated_user_can_signup(self):
        email = 'existing4@example.test'

        old_user = BadgeUser(email=email)  # no password set
        old_user.save()

        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secret',
            'email': email
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    def test_should_signup_with_email_with_plus(self):
        response = self.client.post('/v1/user/profile', {
            'first_name': 'existing',
            'last_name': 'user',
            'password': 'secret',
            'email': 'nonexistent23+extra@test.nonexistent'
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)


class UserUnitTests(TestCase):
    def test_user_can_have_unicode_characters_in_name(self):
        user = BadgeUser(
            username='abc', email='abc@example.com',
            first_name=u'\xe2', last_name=u'Bowie')

        self.assertEqual(user.get_full_name(), u'\xe2 Bowie')


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    },
)
class UserEmailTests(APITestCase):
    fixtures = ['0001_initial_superuser']

    @classmethod
    def tearDownClass(cls):
        c = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        c.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))

        self.badgr_app = BadgrApp(cors='testserver',
                                  email_confirmation_redirect='http://testserver/login/',
                                  forgot_password_redirect='http://testserver/reset-password/')
        self.badgr_app.save()

        self.client.force_authenticate(user=BadgeUser.objects.get(pk=1))
        response = self.client.get('/v1/user/auth-token')
        self.assertEqual(response.status_code, 200)

    def test_user_register_new_email(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        starting_count = len(response.data)

        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(starting_count+1, len(response.data))

    def test_user_can_remove_email(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)

        not_primary = random.choice(filter(lambda e: e['verified'] and not e['primary'], response.data))
        primary = random.choice(filter(lambda e: e['primary'], response.data))

        # cant remove primary email
        response = self.client.delete('/v1/user/emails/{}'.format(primary.get('id')))
        self.assertEqual(response.status_code, 400)
        response = self.client.get('/v1/user/emails/{}'.format(primary.get('id')))
        self.assertEqual(response.status_code, 200)

        # can remove a non-primary email
        response = self.client.delete('/v1/user/emails/{}'.format(not_primary.get('id')))
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/v1/user/emails/{}'.format(not_primary.get('id')))
        self.assertEqual(response.status_code, 404)

    def test_user_can_make_email_primary(self):
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)

        not_primary = random.choice(filter(lambda e: e['verified'] and not e['primary'], response.data))

        # set a non primary email to primary
        response = self.client.put('/v1/user/emails/{}'.format(not_primary.get('id')), {
            'primary': True
        })
        self.assertEqual(response.status_code, 200)

        # confirm that the new email is primary and the others aren't
        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        for email in response.data:
            if email['id'] == not_primary['id']:
                self.assertEqual(email['primary'], True)
            else:
                self.assertEqual(email['primary'], False)

    def test_user_can_resend_verification_email(self):
        # register a new un-verified email
        response = self.client.post('/v1/user/emails', {
            'email': 'new+email@newemail.com',
        })
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        not_verified = random.choice(filter(lambda e: not e['verified'], response.data))
        verified = random.choice(filter(lambda e: e['verified'], response.data))

        # dont resend verification email if already verified
        response = self.client.put('/v1/user/emails/{}'.format(verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)

        # gets an email for an unverified email
        response = self.client.put('/v1/user/emails/{}'.format(not_verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 2)

    def test_user_can_request_forgot_password(self):
        self.client.logout()

        # dont send recovery to unknown emails
        response = self.client.post('/v1/user/forgot-password', {
            'email': 'unknown-test2@example.com.fake',
        })
        self.assertEqual(response.status_code, 200, "Does not leak information about account emails")
        self.assertEqual(len(mail.outbox), 0)

        with self.settings(BADGR_APP_ID=self.badgr_app.id):
            # successfully send recovery email
            response = self.client.post('/v1/user/forgot-password', {
                'email': 'test2@example.com',
            })
            self.assertEqual(response.status_code, 200)
            # received email with recovery url
            self.assertEqual(len(mail.outbox), 1)
            matches = re.search(r'/v1/user/forgot-password\?token=(.*)', mail.outbox[0].body)
            self.assertIsNotNone(matches)
            token = matches.group(1)
            new_password = 'new-password-ee'

            # able to use token received in email to reset password
            response = self.client.put('/v1/user/forgot-password', {
                'token': token,
                'password': new_password
            })
            self.assertEqual(response.status_code, 200)

            response = self.client.post('/api-auth/token', {
                'username': "test2",
                'password': new_password,
            })
            self.assertEqual(response.status_code, 200)

    def test_lower_variant_autocreated_on_new_email(self):
        first_email = CachedEmailAddress(
            email="HelloAgain@world.com", user=BadgeUser.objects.first(), verified=True
        )
        first_email.save()
        self.assertIsNotNone(first_email.pk)

        variants = EmailAddressVariant.objects.filter(canonical_email=first_email)

        self.assertEqual(len(variants), 1)
        self.assertEqual(variants[0].email, 'helloagain@world.com')

    def test_can_create_variants(self):
        first_email = CachedEmailAddress.objects.get(email="test@example.com")
        self.assertIsNotNone(first_email.pk)

        first_variant_email = "TEST@example.com"
        second_variant_email = "Test@example.com"

        first_variant = EmailAddressVariant(email=first_variant_email, canonical_email=first_email)
        first_variant.save()
        self.assertEqual(first_variant.canonical_email, first_email)

        second_variant = first_email.add_variant(second_variant_email)
        self.assertEqual(second_variant.canonical_email, first_email)

        self.assertEqual(len(first_email.emailaddressvariant_set.all()), 2)
        self.assertEqual(len(first_email.cached_variants()), 2)

    def test_user_can_create_variant_method(self):
        user = BadgeUser.objects.first()
        first_email = CachedEmailAddress(
            email="howdy@world.com", user=user, verified=True
        )
        first_email.save()
        first_email.add_variant("HOWDY@world.com")

        self.assertTrue(user.can_add_variant("Howdy@world.com"))
        self.assertFalse(user.can_add_variant("HOWDY@world.com"))  # already exists
        self.assertFalse(user.can_add_variant("howdy@world.com"))  # is the original
        self.assertFalse(user.can_add_variant("howdyfeller@world.com"))  # not a match of original

    def test_cannot_create_variant_for_unconfirmed_email(self):
        new_email_address = "new@unconfirmed.info"
        new_email = CachedEmailAddress.objects.create(email=new_email_address, user=BadgeUser.objects.first())
        new_variant = EmailAddressVariant(email=new_email_address.upper(), canonical_email=new_email)

        try:
            new_variant.save()
        except ValidationError as e:
            self.assertEqual(e.message, "EmailAddress must be verified before registering variants.")
        else:
            self.assertEqual(new_variant.pk, None)  # Save should not have been successful.

    def cannot_link_variant_of_case_insensitive_nonmatch(self):
        first_email = CachedEmailAddress.objects.get(email="test@example.com")
        self.assertIsNotNone(first_email.pk)

        variant_email = "NOMATCH@example.com"

        variant = EmailAddressVariant(email=variant_email, canonical_email=first_email)
        try:
            variant.save()
        except ValidationError as e:
            self.assertEqual(e.message, "New EmailAddressVariant does not match stored email address.")
        else:
            raise self.fail("ValidationError expected on nonmatch.")


@override_settings(
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    },
)
class UserProfileTests(APITestCase):
    fixtures = ['0001_initial_superuser']

    @classmethod
    def tearDownClass(cls):
        c = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        c.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))

    def test_user_can_change_profile(self):
        first = 'firsty'
        last = 'lastington'
        new_password = 'new-password'
        username = 'testinguser'
        original_password = 'password'

        user = BadgeUser(username=username, is_active=True)
        user.set_password(original_password)
        user.save()
        self.client.login(username=username, password=original_password)
        self.assertUserLoggedIn()

        response = self.client.put('/v1/user/profile', {
            'first_name': first,
            'last_name': last,
            'password': new_password,
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(first, response.data.get('first_name'))
        self.assertEqual(last, response.data.get('last_name'))

        self.client.logout()
        self.client.login(username=username, password=new_password)
        self.assertUserLoggedIn()
        self.assertEqual(len(mail.outbox), 1)

    def assertUserLoggedIn(self, user_pk=None):
        self.assertIn(SESSION_KEY, self.client.session)
        if user_pk is not None:
            self.assertEqual(self.client.session[SESSION_KEY], user_pk)
            
