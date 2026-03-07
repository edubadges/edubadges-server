from typing import Any, Optional
from unittest.mock import patch

from django.core.handlers.wsgi import WSGIRequest
from issuer.models import BadgeInstance
from mainsite.tests import BadgrTestCase


class OB3CallbackAPITest(BadgrTestCase):
    """
    Tests for the OB3 callback endpoint that returns OpenBadge v3 serialization
    of a badge instance.
    """

    def test_callback_endpoint_returns_ob3_credential(self):
        """
        Test that the callback endpoint returns a valid OB3 credential for a badge instance.
        - Make POST request to /v1/ob3/callback/
        - Verify response contains required OB3 credential fields
        """
        assertion = self._setup_assertion_with_relations()
        response = self._post_callback(assertion.entity_id, str(assertion.get_email_address()))

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Check top-level credential structure
        self.assertIn('id', response_data)
        self.assertIn('issuer', response_data)
        self.assertIn('credentialSubject', response_data)

        # Check issuer structure
        issuer_data: dict[str, Any] = response_data['issuer']
        self.assertIn('id', issuer_data)
        self.assertIn('type', issuer_data)
        self.assertIn('name', issuer_data)
        self.assertEqual(issuer_data['type'], ['Profile'])

        # Check credentialSubject structure
        credential_subject: dict[str, Any] = response_data['credentialSubject']
        self.assertIn('type', credential_subject)
        self.assertIn('achievement', credential_subject)
        self.assertEqual(credential_subject['type'], ['AchievementSubject'])

        # Check achievement structure
        achievement = credential_subject['achievement']
        self.assertIn('id', achievement)
        self.assertIn('type', achievement)
        self.assertIn('criteria', achievement)
        self.assertIn('description', achievement)
        self.assertIn('name', achievement)
        self.assertIn('image', achievement)
        self.assertEqual(achievement['type'], ['Achievement'])

        # Check criteria structure
        self.assertIn('narrative', achievement['criteria'])

        # Check image structure
        self.assertIn('type', achievement['image'])
        self.assertIn('id', achievement['image'])
        self.assertEqual(achievement['image']['type'], 'Image')

    def test_callback_endpoint_with_recipient_identifier(self):
        """
        Test that the callback endpoint includes hashed recipient identifier when present.
        """
        assertion = self._setup_assertion_with_relations()
        response = self._post_callback(assertion.entity_id, str(assertion.get_email_address()))

        # Verify response
        self.assertEqual(response.status_code, 200)
        response_data = response.json()

        # Check identifier structure
        identifier = response_data['credentialSubject']['identifier'][0]
        self.assertEqual(identifier['type'], 'IdentityObject')
        self.assertEqual(identifier['hashed'], True)
        self.assertEqual(identifier['identityType'], 'emailAddress')
        self.assertIn('identityHash', identifier)
        self.assertIn('salt', identifier)
        self.assertTrue(identifier['identityHash'].startswith('sha256$'))

    def test_callback_endpoint_nonexistent_badge_returns_404(self):
        """
        Test that requesting a non-existent badge instance returns 404.
        """
        response = self._post_callback('nonexistent-badge-entity-id', 'test@example.com')
        self.assertEqual(response.status_code, 404)

    def test_callback_endpoint_anonymous_access(self):
        """
        Test that requesting a badge instance needs no bearer token authentication.
        """
        assertion = self._setup_assertion_with_relations()
        self.client.logout()
        response = self._post_callback(assertion.entity_id, assertion.get_email_address())
        self.assertEqual(response.status_code, 200)

    def test_callback_endpoint_requires_issuer_state_parameter(self):
        """
        Test that the callback endpoint requires an issuer_state parameter.
        If parameter is missing, should return 400 Bad Request.
        """
        response = self._post_callback(None, 'test@example.com')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ['issuer_state parameter is required'])

    def test_callback_endpoint_requires_email_parameter(self):
        """
        Test that the callback endpoint requires an email parameter.
        If parameter is missing, should return 403 Bad Request.
        """
        response = self._post_callback('issuer_state', None,)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), ['email parameter is required'])

    def test_callback_endpoint_must_be_for_recipient_user(self):
        """
        Test that the callback endpoint must be for the user who initiated the request.
        If the sub parameter does not match the uuid of the socialaccount
        for the user who initiated the request, should return 403 Forbidden.
        """
        assertion = self._setup_assertion_with_relations()
        another_user = self.setup_student(authenticate=False)
        response = self._post_callback(assertion.entity_id, another_user.email)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'invalid email'})

    def test_callback_endpoint_must_be_for_existing_user(self):
        """
        Test that the callback endpoint must be for an existing user.
        If the sub parameter does not match the uuid of any socialaccount for the user who initiated the request,
        should return 403 Forbidden.
        """
        assertion = self._setup_assertion_with_relations()
        response = self._post_callback(assertion.entity_id, 'nonexistent@example.com')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {'detail': 'unknown email'})

    def _post_callback(self, issuer_state: Optional[str], email: Optional[str]) -> WSGIRequest:
        """Helper method to make POST requests to the callback endpoint."""

        data: dict[str, str] = {}
        if issuer_state is not None:
            data['issuer_state'] = issuer_state
        if email is not None:
            data['email'] = email

        # An example of the actual body that the veramo issuer sends to the callback:
        # {
        #   "acr": "urn:oasis:names:tc:SAML:2.0:ac:classes:Password",
        #   "authenticating_authority": "https://login.test.eduid.nl",
        #   "eduperson_affiliation": ["member", "student", "affiliate"],
        #   "eduperson_assurance": [
        #     "https://refeds.org/assurance/IAP/medium",
        #     "https://eduid.nl/validated/institution",
        #     "https://refeds.org/assurance",
        #     "https://refeds.org/assurance/ID/unique",
        #     "https://refeds.org/assurance/ID/eppn-unique-no-reassign",
        #     "https://refeds.org/assurance/IAP/low",
        #     "https://refeds.org/assurance/version/2",
        #     "https://eduid.nl/validated/email-validated"
        #   ],
        #   "eduperson_scoped_affiliation": [
        #     "member@mbob.nl",
        #     "student@mbob.nl",
        #     "affiliate@eduid.nl"
        #   ],
        #   "email": "ber@xxxxxx",
        #   "email_verified": true,
        #   "family_name": "Kuester",
        #   "given_name": "Markus",
        #   "name": "B\u00e8r Kuester",
        #   "schac_home_organization": "eduid.nl",
        #   "sub": "1axxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        #   "updated_at": 1772708164,
        #   "issuer_state": "nxxxxxxxxxxxxxxxxxxxxx",
        #   "iss": "https://oauth2-server.playground.sdp.surf.nl"
        # }
        return self.client.post('/ob3/v1/ob3/callback', data)

    def _setup_assertion_with_relations(self) -> BadgeInstance:
        teacher = self.setup_teacher(authenticate=False)
        student = self.setup_student(authenticate=False)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher)
        return assertion


class OB3CredentialsViewAPITest(BadgrTestCase):
    """
    Tests for the OB3 CredentialsView endpoint that issues credentials.
    """

    def _with_mock_endpoints(self):
        """
        Context manager that mocks all HTTP requests.post calls to return successful responses.
        This avoids making actual network requests during tests.
        """
        # Create a mock response object
        mock_response = type(
            'MockResponse',
            (),
            {'status_code': 200, 'text': '{"fake": "json"}', 'json': lambda self: {'uri': 'oidc://fake-offer-uri'}},
        )()

        # Return the patch object as a context manager
        return patch('ob3.models.requests.post', return_value=mock_response)

    def test_credentials_endpoint_returns_offer_for_authorization_variant(self):
        """
        Test that the credentials endpoint returns an offer for the authorization variant.
        """
        assertion = self._setup_assertion_with_relations()

        # Mock the HTTP calls to avoid actual network requests
        with self._with_mock_endpoints():
            response = self._post_credentials(assertion.id, 'authorization')

            self.assertEqual(response.status_code, 201)
            response_data = response.json()
            self.assertIn('offer', response_data)

    def test_credentials_endpoint_returns_offer_for_preauthorized_variant(self):
        """
        Test that the credentials endpoint returns an offer for the preauthorized variant.
        """
        assertion = self._setup_assertion_with_relations()

        # Mock the HTTP calls to avoid actual network requests
        with self._with_mock_endpoints():
            response = self._post_credentials(assertion.id, 'preauthorized')
            self.assertResponseCode(response, 201)
            response_data = response.json()
            self.assertIn('offer', response_data)

    def test_credentials_endpoint_requires_badge_id(self):
        """
        Test that the credentials endpoint requires a badge_id parameter.
        """
        with self._with_mock_endpoints():
            self.setup_student(authenticate=True)
            response = self._post_credentials(None, 'authorization')
            self.assertResponseCode(response, 400)

    def test_credentials_endpoint_falls_back_to_veramo(self):
        """
        Test that the credentials endpoint falls back to veramo if no variant is provided.
        """
        with self._with_mock_endpoints():
            assertion = self._setup_assertion_with_relations()
            response = self._post_credentials(assertion.id, None)
            self.assertResponseCode(response, 201)
            self.assertEqual(response.json()['offer'], 'oidc://fake-offer-uri')

    def test_credentials_endpoint_requires_valid_variant(self):
        """
        Test that the credentials endpoint requires a valid variant.
        """
        with self._with_mock_endpoints():
            assertion = self._setup_assertion_with_relations()
            response = self._post_credentials(assertion.id, 'invalid-variant')
            self.assertResponseCode(response, 400)

    def test_credentials_endpoint_requires_existing_badge(self):
        """
        Test that the credentials endpoint requires an existing badge instance.
        """
        with self._with_mock_endpoints():
            self.setup_student(authenticate=True)
            response = self._post_credentials(999999, 'authorization')
            self.assertResponseCode(response, 404)

    def test_credentials_endpoint_requires_user_owns_badge(self):
        """
        Test that the credentials endpoint requires the user to own the badge.
        """
        with self._with_mock_endpoints():
            assertion = self._setup_assertion_with_relations()
            self.setup_student(authenticate=True)

            response = self._post_credentials(assertion.id, 'authorization')
            self.assertResponseCode(response, 404)

    def test_credentials_endpoint_returns_offer_for_veramo_variant(self):
        """
        Test that the credentials endpoint returns an offer for the veramo variant.
        """
        assertion = self._setup_assertion_with_relations()

        # Mock the HTTP calls to avoid actual network requests
        with self._with_mock_endpoints():
            response = self._post_credentials(assertion.id, 'veramo')

            self.assertEqual(response.status_code, 201)
            response_data = response.json()
            self.assertIn('offer', response_data)

    def assertResponseCode(self, response, expected_code):
        self.assertEqual(
            response.status_code,
            expected_code,
            f'Expected status code {expected_code}, got {response.status_code}. {response.content.decode("utf-8")}',
        )

    def _post_credentials(self, badge_id: int, variant: str):
        """Helper method to make POST requests to the credentials endpoint."""
        data: dict[str, Any] = {'badge_id': badge_id, 'variant': variant}
        # Filter out None values
        data = {k: v for k, v in data.items() if v is not None}
        return self.client.post('/ob3/v1/ob3', data)

    def _setup_assertion_with_relations(self) -> BadgeInstance:
        teacher = self.setup_teacher(authenticate=False)
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher)
        return assertion
