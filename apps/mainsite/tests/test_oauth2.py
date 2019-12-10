import json

from badgeuser.authcode import encrypt_authcode, decrypt_authcode, authcode_for_accesstoken
from badgeuser.models import BadgrAccessToken
from django.urls import reverse
from mainsite.models import ApplicationInfo
from mainsite.tests import BadgrTestCase
from mainsite.tests.base import SetupPermissionHelper
from oauth2_provider.models import AccessToken, Application


class OAuth2TokenTests(SetupPermissionHelper, BadgrTestCase):
    #@unittest.skip('For debug speedup')
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
        ApplicationInfo.objects.create(
            application=application,
            allowed_scopes='rw:issuer'
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

    #@unittest.skip('For debug speedup')
    def test_can_rw_issuer_with_token(self):
        client_id = "test"
        client_secret = "secret"
        test_group = self.setup_faculty_admin_group()
        client_user = self.setup_user(authenticate=False, groups=[test_group], teacher=True)
        application = Application.objects.create(
            client_id=client_id,
            client_secret=client_secret,
            user=client_user,
            authorization_grant_type=Application.GRANT_CLIENT_CREDENTIALS,
            name='test client app'
        )
        ApplicationInfo.objects.create(
            application=application,
            allowed_scopes='rw:issuer'
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
            data=json.dumps({'name': 'Another Issuer', 'url': 'http://a.com/b', 'email': client_user.email}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)

    #@unittest.skip('For debug speedup')
    def test_can_encrypt_decrypt_authcode(self):
        payload = "fakeentityid"
        code = encrypt_authcode(payload)
        decrypted_payload = decrypt_authcode(code)
        self.assertEqual(payload, decrypted_payload)

    #@unittest.skip('For debug speedup')
    def test_can_use_authcode_exchange(self):
        user = self.setup_user(authenticate=True)
        application = Application.objects.create(
            client_id='testing-authcode',
            client_type=Application.CLIENT_PUBLIC,
            authorization_grant_type=Application.GRANT_PASSWORD
        )
        ApplicationInfo.objects.create(application=application)
        accesstoken = BadgrAccessToken.objects.generate_new_token_for_user(user, application=application, scope='r:profile')

        # can exchange valid authcode for accesstoken
        authcode = authcode_for_accesstoken(accesstoken)
        response = self.client.post(reverse('oauth2_code_exchange'), dict(code=authcode))
        self.assertEqual(response.status_code, 200)
        self.assertDictContainsSubset({'access_token': accesstoken.token}, response.data)

        # cant exchange invalid authcode
        response = self.client.post(reverse('oauth2_code_exchange'), dict(code="InvalidAuthCode"))
        self.assertEqual(response.status_code, 400)

        # cant exchange expired authcode
        expired_authcode = authcode_for_accesstoken(accesstoken, expires_seconds=0)
        response = self.client.post(reverse('oauth2_code_exchange'), dict(code=expired_authcode))
        self.assertEqual(response.status_code, 400)

