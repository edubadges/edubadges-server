import urllib

from django.urls import reverse
from oauth2_provider.models import Application

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
