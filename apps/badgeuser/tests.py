from django.core import mail

from rest_framework.authtoken.models import Token
from rest_framework.test import APIRequestFactory, APITestCase
from badgeuser.models import BadgeUser

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
