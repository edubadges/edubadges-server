import os
import random
import time

from django.core import mail
from django.core.cache.backends.filebased import FileBasedCache
from django.test import TestCase, override_settings
from django.core.cache import cache

from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase

from mainsite import TOP_DIR
from .models import BadgeUser
from .serializers import UserProfileField

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
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'unclaimed1@example.com',
            'password': '123456'
        }

        response = self.client.post('/v1/user/profile', user_data)

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

        response = self.client.get('/v1/user/emails')
        self.assertEqual(response.status_code, 200)
        not_verified = random.choice(filter(lambda e: not e['verified'], response.data))
        verified = random.choice(filter(lambda e: e['verified'], response.data))

        # dont resend verification email if already verified
        response = self.client.put('/v1/user/emails/{}'.format(verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)

        # gets an email for an unverified email
        response = self.client.put('/v1/user/emails/{}'.format(not_verified.get('id')), {
            'resend': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)


