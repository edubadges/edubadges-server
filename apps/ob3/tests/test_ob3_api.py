from typing import Any

from allauth.socialaccount.models import SocialAccount
from badgeuser.models import BadgeUser
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
        recipient_uid: str = self._get_social_account(assertion.user).uid

        # Make request to callback endpoint with state parameter
        response = self._post_callback(assertion.entity_id, recipient_uid)

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
        recipient_uid: str = self._get_social_account(assertion.user).uid
        response = self._post_callback(assertion.entity_id, recipient_uid)

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
        response = self._post_callback('nonexistent-badge-entity-id', '42')
        self.assertEqual(response.status_code, 404)

    def test_callback_endpoint_anonymous_access(self):
        """
        Test that requesting a badge instance needs no authentication.
        """
        assertion = self._setup_assertion_with_relations()
        self.client.logout()
        recipient_uid: str = self._get_social_account(assertion.user).uid
        response = self._post_callback(assertion.entity_id, recipient_uid)
        self.assertEqual(response.status_code, 200)

    def test_callback_endpoint_requires_state_parameter(self):
        """
        Test that the callback endpoint requires a state parameter.
        If state parameter is missing, should return 400 Bad Request.
        """
        response = self.client.post('/ob3/v1/ob3/callback', {'user_id': '42'})
        self.assertEqual(response.status_code, 400)

    def test_callback_endpoint_requires_user_id_parameter(self):
        """
        Test that the callback endpoint requires a user_id parameter.
        If user_id parameter is missing, should return 400 Bad Request.
        """
        response = self.client.post('/ob3/v1/ob3/callback', {'state': '123'})
        self.assertEqual(response.status_code, 400)

    def test_callback_endpoint_must_be_for_user(self):
        """
        Test that the callback endpoint must be for the user who initiated the request.
        If the user_id parameter does not match the uuid of the socialaccount
        for the user who initiated the request, should return 403 Forbidden.
        """
        assertion = self._setup_assertion_with_relations()
        another_user = self.setup_student(authenticate=False)
        response = self.client.post(
            '/ob3/v1/ob3/callback',
            {'state': assertion.entity_id, 'user_id': self._get_social_account(another_user).uid},
        )
        self.assertEqual(response.status_code, 403)

    def test_callback_endpoint_can_be_for_any_socialaccount_uuid(self):
        """
        Test that the callback endpoint must be for any socialaccount uuid of the user who initiated the request.
        If the user_id parameter does not match the uuid of any socialaccount for the user who initiated the request,
        should return 403 Forbidden.
        """
        assertion = self._setup_assertion_with_relations()
        second_social_account = self.add_eduid_socialaccount(assertion.user)

        self.assertEqual(SocialAccount.objects.filter(user=assertion.user).count(), 2)
        response = self.client.post(
            '/ob3/v1/ob3/callback', {'state': assertion.entity_id, 'user_id': second_social_account.uid}
        )
        self.assertEqual(response.status_code, 200, response.content)

    def _post_callback(self, state: str, user_id: str):
        """Helper method to make POST requests to the callback endpoint."""
        data: dict[str, str] = {'state': state, 'user_id': user_id}
        return self.client.post('/ob3/v1/ob3/callback', data)

    def _setup_assertion_with_relations(self) -> BadgeInstance:
        teacher = self.setup_teacher(authenticate=False)
        student = self.setup_student(authenticate=False)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher)
        return assertion

    def _get_social_account(self, user: BadgeUser) -> SocialAccount:
        return SocialAccount.objects.get(user=user)
