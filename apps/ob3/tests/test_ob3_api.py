from typing import Any
from mainsite.tests import BadgrTestCase

class OB3CallbackAPITest(BadgrTestCase):
    """
    Tests for the OB3 callback endpoint that returns OpenBadge v3 serialization
    of a badge instance.
    """

    def test_callback_endpoint_returns_ob3_credential(self):
        """
        Test that the callback endpoint returns a valid OB3 credential for a badge instance.
        - Make GET request to /v1/ob3/callback/{badgeinstance_identifier}
        - Verify response contains required OB3 credential fields
        """
        assertion = self._setup_assertion_with_relations()

        # Make request to callback endpoint
        response = self.client.post(f'/ob3/v1/ob3/callback/{assertion.entity_id}')

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
        # Make request to callback endpoint
        response = self.client.post(f'/ob3/v1/ob3/callback/{assertion.entity_id}')

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
        response = self.client.post('/ob3/v1/ob3/callback/nonexistent-badge-id')
        self.assertEqual(response.status_code, 404)

    def test_callback_endpoint_anonymous_access(self):
        """
        Test that requesting a badge instance needs no authentication.
        """
        assertion = self._setup_assertion_with_relations()
        self.client.logout()
        response = self.client.post(f'/ob3/v1/ob3/callback/{assertion.entity_id}')
        self.assertEqual(response.status_code, 200)
       
    def _setup_assertion_with_relations(self):
        teacher = self.setup_teacher(authenticate=False)
        student = self.setup_student(authenticate=False)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher)
        return assertion
