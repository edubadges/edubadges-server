import urllib

from django.urls import reverse
from oauth2_provider.models import AccessToken, Application

from issuer.models import Issuer
from mainsite.models import ApplicationInfo
from mainsite.tests import BadgrTestCase


class OAuth2TokenTests(BadgrTestCase):
    def test_client_credentials_can_get_token(self):
        client_id = "test"
        client_secret = "secret"
        client_user = self.setup_user(authenticate=False)
        application = Application.objects.create(
            client_id=client_id,
            client_secret=client_secret,
            user=client_user,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            name='test client app'
        )

        request_data = dict(
            grant_type='client_credentials',
            client_id=application.client_id,
            client_secret=client_secret,
            scope='rw:issuer'
        )
        response = self.client.post(reverse('oauth2_provider_token'), data=request_data)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('oauth2_provider_token'), data=request_data)
        self.assertEqual(response.status_code, 200)

    def test_can_rw_issuer_with_token(self):
        client_id = "test"
        client_secret = "secret"
        client_user = self.setup_user(authenticate=False)
        application = Application.objects.create(
            client_id=client_id,
            client_secret=client_secret,
            user=client_user,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            name='test client app'
        )

        request_data = dict(
            grant_type='client_credentials',
            client_id=application.client_id,
            client_secret=client_secret,
            scope='rw:issuer'
        )
        response = self.client.post(reverse('oauth2_provider_token'), data=request_data)
        self.assertEqual(response.status_code, 200)
        first_token = response.json()['access_token']
        first_token_instance = AccessToken.objects.get(token=first_token)

        # Do it again... The token should update its "token" value.
        response = self.client.post(reverse('oauth2_provider_token'), data=request_data)
        self.assertEqual(response.status_code, 200)

        token = response.json()['access_token']
        new_token_instance = AccessToken.objects.get(token=token)
        # self.assertEqual(first_token_instance.pk, new_token_instance.pk)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(token))
        response = self.client.post(
            reverse('v2_api_issuer_list'),
            data={'name': 'Another Issuer', 'url': 'http://a.com/b', 'email': client_user.email}
        )
        self.assertEqual(response.status_code, 201)
