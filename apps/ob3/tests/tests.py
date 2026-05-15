from datetime import datetime as DateTime
from typing import Any, Optional, Union
from unittest.mock import patch

from django.test import SimpleTestCase
from django.urls import reverse
from mainsite.settings import DEFAULT_DOMAIN, UI_URL
from ob3.models import IdentityObject, ImpierceOfferRequest, VeramoOfferRequest
from ob3.models import SphereonOfferRequest as SphereonOfferRequest
from ob3.serializers import ImpierceOfferRequestSerializer as OfferRequestSerializer


class BadgeClassMock:
    def __init__(self):
        self.criteria_text: str = 'You must Lorem Ipsum, **dolor** _sit_ amet'
        self.description: str = 'This badge is a Lorem Ipsum, **dolor** _sit_ amet'
        self.name: str = 'Mock Badge'
        self.issuer: IssuerMock = IssuerMock()
        self.participation: Optional[str] = None
        self.alignment_items: list[AligmentItemMock] = []
        self.extension_items: dict[str, dict[str, Union[str, int, float]]] = {}

    def image_url(self):
        return 'https://example.com/images/mock.png'


class BadgeInstanceMock:
    def __init__(self):
        self.entity_id: str = 'BADGE1234'
        self.salt: Optional[str] = None
        self.recipient_identifier: Optional[str] = None

        self.badgeclass: BadgeClassMock = BadgeClassMock()
        self.issued_on: Optional[DateTime] = None
        self.expires_at: Optional[DateTime] = None


class InstitutionMock:
    def __init__(self):
        self.entity_id: str = 'INST1234'
        self.name: str = 'Mock Institution'

    def image_url(self):
        return 'https://example.com/images/institutions/mock.png'


class FacultyMock:
    def __init__(self):
        self.entity_id: str = 'FAC1234'
        self.name: str = 'Mock Faculty'
        self.institution: InstitutionMock = InstitutionMock()

    def image_url(self):
        return 'https://example.com/images/faculties/mock.png'


class IssuerMock:
    def __init__(self):
        self.entity_id: str = 'ISS1234'
        self.name: str = 'Mock Issuer'
        self.faculty: FacultyMock = FacultyMock()

    def image_url(self) -> str:
        return 'https://example.com/images/issuers/mock.png'


class AligmentItemMock:
    def __init__(self):
        self.target_name: str = 'interne geneeskunde'
        self.target_url: str = 'https://example.com/esco/1337'
        self.target_code: str = '1337'
        self.target_framework: str = 'ESCO'
        self.target_description: str = '# example cool'


def mock_hasher(_id: str, _salt: str):
    return 'mock_hash'


class TestCredentialsSerializers(SimpleTestCase):
    def test_serializer_serializes_credential(self):
        badge_instance = BadgeInstanceMock()
        actual_data = self._serialize_it(badge_instance)
        expected_data = {
            'offerId': 'offer_id',
            'expiresAt': 'never',
            'credentialConfigurationId': 'credential_configuration_id',
            'credential': {
                'id': f'{UI_URL}/public/assertions/BADGE1234',
                'issuer': {
                    'id': f'{UI_URL}/ob3/issuers/ISS1234',
                    'type': ['Profile'],
                    'name': 'Mock Issuer',
                    'image': {'type': 'Image', 'id': 'https://example.com/images/issuers/mock.png'},
                },
                'credentialSubject': {
                    'type': ['AchievementSubject'],
                    'achievement': {
                        'id': f'{UI_URL}/public/assertions/BADGE1234',
                        'type': ['Achievement'],
                        'criteria': {'narrative': 'You must Lorem Ipsum, **dolor** _sit_ amet'},
                        'description': 'This badge is a Lorem Ipsum, **dolor** _sit_ amet',
                        'name': 'Mock Badge',
                        'image': {'type': 'Image', 'id': 'https://example.com/images/mock.png'},
                        'creator': {
                            'type': ['Profile'],
                            'id': f'{UI_URL}/public/faculties/FAC1234',
                            'name': 'Mock Faculty',
                            'image': {'type': 'Image', 'id': 'https://example.com/images/faculties/mock.png'},
                            'parentOrg': {
                                'type': ['Profile'],
                                'id': f'{UI_URL}/public/institutions/INST1234',
                                'name': 'Mock Institution',
                                'image': {'type': 'Image', 'id': 'https://example.com/images/institutions/mock.png'},
                            },
                        },
                    },
                },
            },
        }

        self.maxDiff: Union[None, bool, int] = None  # Debug full diff
        self.assertDictEqual(actual_data, expected_data)

    def test_recipient(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.recipient_identifier = '1234abc123abc'
        badge_instance.salt = 's@lt'
        actual_data = self._serialize_it(badge_instance)
        expected_identifier = {
            'type': 'IdentityObject',
            'hashed': True,
            'identityHash': 'sha256$a2441d313d3d31514464ed6732d255df3391cbc85dd374d8a94b683248dcb7b8',
            'identityType': 'emailAddress',
            'salt': 's@lt',
        }
        self.assertEqual(len(actual_data['credential']['credentialSubject']['identifier']), 1)
        self.assertEqual(actual_data['credential']['credentialSubject']['identifier'][0], expected_identifier)

    def test_issuer(self):
        badge_instance = BadgeInstanceMock()
        actual_data = self._serialize_it(badge_instance)
        expected_issuer = {
            'id': 'http://localhost:8080/ob3/issuers/ISS1234',
            'type': ['Profile'],
            'name': 'Mock Issuer',
            'image': {'type': 'Image', 'id': 'https://example.com/images/issuers/mock.png'},
        }
        self.assertEqual(actual_data['credential']['issuer'], expected_issuer)

    def test_creator(self):
        badge_instance = BadgeInstanceMock()
        actual_data = self._serialize_it(badge_instance)

        expected_data = {
            'type': ['Profile'],
            'id': 'http://localhost:8080/public/faculties/FAC1234',
            'name': 'Mock Faculty',
            'image': {'type': 'Image', 'id': 'https://example.com/images/faculties/mock.png'},
            'parentOrg': {
                'type': ['Profile'],
                'id': 'http://localhost:8080/public/institutions/INST1234',
                'name': 'Mock Institution',
                'image': {'type': 'Image', 'id': 'https://example.com/images/institutions/mock.png'},
            },
        }

        self.maxDiff: Union[int, None] = None
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['creator'], expected_data)

    def test_optional_valid_from_field_set(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.issued_on = DateTime.fromisoformat('2020-01-01:01:13:37')
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data['credential']['validFrom'], '2020-01-01T01:13:37Z')

    def test_optional_valid_from_field_notset(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.issued_on = None
        actual_data = self._serialize_it(badge_instance)

        self.assertNotIn('validFrom', actual_data)

    def test_optional_valid_until(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = DateTime.fromisoformat('2020-01-01:01:13:37')
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data['credential']['validUntil'], '2020-01-01T01:13:37Z')

    def test_impierce_offer_request_expires_at(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = DateTime.fromisoformat('2020-01-01:01:13:37')
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data['expiresAt'], '2020-01-01T01:13:37Z')

    def test_impierce_offer_request_expires_at_notset(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = None
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data['expiresAt'], 'never')

    def test_education_language_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {'extensions:LanguageExtension': {'Language': 'en_EN'}}
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['inLanguage'], 'en_EN')

    def test_ects_extension_int(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {'extensions:ECTSExtension': {'ECTS': int(1)}}
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['ECTS'], 1.0)

    def test_ects_extension_float(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {'extensions:ECTSExtension': {'ECTS': float(2.5)}}
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['ECTS'], 2.5)

    def test_ects_extension_one_place(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {'extensions:ECTSExtension': {'ECTS': float(2.54321)}}
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['ECTS'], 2.5)

    def test_ects_extension_max_999(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {'extensions:ECTSExtension': {'ECTS': float(240.0)}}
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['ECTS'], 240)

    def test_education_program_identifier_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
            'extensions:EducationProgramIdentifierExtension': {'EducationProgramIdentifier': '1234'}
        }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(
            actual_data['credential']['credentialSubject']['achievement']['educationProgramIdentifier'], '1234'
        )

    def test_participation_type(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.participation = 'blended'

        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data['credential']['credentialSubject']['achievement']['participationType'], 'blended')

    def test_aligments(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.alignment_items = [AligmentItemMock()]
        actual_data = self._serialize_it(badge_instance)
        actual_data = actual_data['credential']['credentialSubject']['achievement']
        expected_alignment = {
            'type': ['Alignment'],
            'targetType': 'ext:ESCOAlignment',
            'targetName': 'interne geneeskunde',
            'targetDescription': '# example cool',
            'targetUrl': 'https://example.com/esco/1337',
            'targetCode': '1337',
        }

        self.assertIn(expected_alignment, actual_data['alignment'])

    def _serialize_it(self, badge_instance: BadgeInstanceMock) -> dict[str, Any]:  # pyright: ignore[reportExplicitAny] BK: Serialize data is too complex for our poorly typed codebase
        # TODO: We should test both impierce and sphereon models and serializers
        edu_credential = ImpierceOfferRequest('offer_id', 'credential_configuration_id', badge_instance)
        return dict(OfferRequestSerializer(edu_credential).data)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType] BK: serailzie data too complex


class TestCredentialModels(SimpleTestCase):
    def test_identity_object_adds_identity_hash_from_hasher(self):
        subject = IdentityObject('1234abc123abc', 's@lt', hasher=mock_hasher)
        self.assertEqual(subject.identity_hash, 'mock_hash')

    def test_identity_object_adds_algorithm_identifier(self):
        subject = IdentityObject('1234abc123abc', 's@lt')
        self.assertTrue(subject.identity_hash.startswith('sha256$'))

    def test_identity_object_adds_salt(self):
        subject_one = IdentityObject('1234abc123abc', '1')
        subject_two = IdentityObject('1234abc123abc', '2')
        self.assertNotEqual(subject_one.identity_hash, subject_two.identity_hash)

    def test_identity_object_ignores_case_in_recipient_identifier(self):
        subject_lower = IdentityObject('1234abc123abc', 's@lt')
        subject_upper = IdentityObject('1234ABC123ABC', 's@lt')
        self.assertEqual(subject_lower.identity_hash, subject_upper.identity_hash)


class TestOfferRequestCallMethods(SimpleTestCase):
    """Test the call() methods of the OfferRequest classes."""

    def test_sphereon_offer_request_call_method(self):
        """Test that SphereonOfferRequest.call() makes the correct HTTP call."""
        badge_instance = BadgeInstanceMock()
        offer_request = SphereonOfferRequest(
            offer_id='test-offer-id',
            credential_configuration_id='OpenBadgeCredential',
            badge_instance=badge_instance,
            edu_id='test-edu-id',
            email='test@example.com',
            eppn='test-eppn',
            family_name='Test',
            given_name='User',
        )
        offer_request.set_url('https://test-sphereon-url.com')
        offer_request.set_authz_token('test-auth-token')

        with patch('ob3.models.requests.post') as mock_post:
            mock_response = type('MockResponse', (), {'status_code': 200, 'text': 'mock-offer-response'})()
            mock_post.return_value = mock_response
            result = offer_request.call()

            mock_post.assert_called_once()
            call_args = mock_post.call_args

            self.assertEqual(call_args[1]['url'], 'https://test-sphereon-url.com')

            headers = call_args[1]['headers']
            self.assertEqual(headers['Accept'], 'application/json')
            self.assertEqual(headers['Authorization'], 'Bearer test-auth-token')

            # Check that serializer was used (indirectly by checking the payload structure)
            payload = call_args[1]['json']
            self.assertIn('credential_configuration_ids', payload)
            self.assertIn('grants', payload)
            self.assertIn('eduId', payload)

            self.assertEqual(result, 'mock-offer-response')

    def test_impierce_offer_request_call_method(self):
        """Test that ImpierceOfferRequest.call() makes the correct HTTP calls."""
        badge_instance = BadgeInstanceMock()
        offer_request = ImpierceOfferRequest(
            offer_id='test-offer-id', credential_configuration_id='openbadge_credential', badge_instance=badge_instance
        )
        offer_request.set_url('https://test-unime-url.com')

        with patch('ob3.models.requests.post') as mock_post:
            # First call (issue credential)
            mock_response1 = type('MockResponse', (), {'status_code': 200, 'text': 'mock-credential-response'})()
            # Second call (get offer)
            mock_response2 = type('MockResponse', (), {'status_code': 200, 'text': 'mock-offer-response'})()
            mock_post.side_effect = [mock_response1, mock_response2]
            result = offer_request.call()
            self.assertEqual(mock_post.call_count, 2)

            # Check first call (issue credential)
            first_call = mock_post.call_args_list[0]
            self.assertIn('/credentials', first_call[1]['url'])
            self.assertEqual(first_call[1]['headers']['Accept'], 'application/json')

            # Check second call (get offer)
            second_call = mock_post.call_args_list[1]
            self.assertIn('/offers', second_call[1]['url'])
            self.assertEqual(second_call[1]['json']['offerId'], 'test-offer-id')

            self.assertEqual(result, 'mock-offer-response')

    def test_sphereon_offer_request_call_method_error_handling(self):
        """Test that SphereonOfferRequest.call() handles HTTP errors correctly."""
        badge_instance = BadgeInstanceMock()
        offer_request = SphereonOfferRequest(
            offer_id='test-offer-id',
            credential_configuration_id='OpenBadgeCredential',
            badge_instance=badge_instance,
            edu_id='test-edu-id',
            email='test@example.com',
            eppn='test-eppn',
            family_name='Test',
            given_name='User',
        )
        offer_request.set_url('https://test-sphereon-url.com')
        offer_request.set_authz_token('test-auth-token')

        with patch('ob3.models.requests.post') as mock_post:
            mock_response = type('MockResponse', (), {'status_code': 400, 'text': 'mock-error-response'})()
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as context:
                _ = offer_request.call()

            self.assertIn('Failed to issue badge', str(context.exception))
            self.assertIn('400', str(context.exception))
            self.assertIn('mock-error-response', str(context.exception))

    def test_impierce_offer_request_call_method_error_handling(self):
        """Test that ImpierceOfferRequest.call() handles HTTP errors correctly."""
        badge_instance = BadgeInstanceMock()
        offer_request = ImpierceOfferRequest(
            offer_id='test-offer-id', credential_configuration_id='openbadge_credential', badge_instance=badge_instance
        )
        offer_request.set_url('https://test-unime-url.com')
        with patch('ob3.models.requests.post') as mock_post:
            mock_response = type('MockResponse', (), {'status_code': 500, 'text': 'mock-server-error'})()
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as context:
                _ = offer_request.call()

            self.assertIn('Failed to issue badge', str(context.exception))
            self.assertIn('500', str(context.exception))
            self.assertIn('mock-server-error', str(context.exception))

    def test_veramo_offer_request_call_method(self):
        """Test that VeramoOfferRequest.call() works correctly."""
        badge_instance = BadgeInstanceMock()
        callback_url = DEFAULT_DOMAIN + reverse('ob3:callback')
        # sanity check
        expected_callback_url = 'http://0.0.0.0:8000/ob3/v1/ob3/callback'
        self.assertEqual(
            callback_url,
            expected_callback_url,
            "Callback URL does not match. Probably DEFAULT_DOMAIN set to something other than 'http://0.0.0.0:8000'",
        )

        offer_request = VeramoOfferRequest('test-credential-config-id', badge_instance, callback_url)  # pyright: ignore[reportArgumentType] BK: Our mocks don't inherit from the class they mock nor do both implement an interface or superclass
        offer_request.set_url('http://test-url.com')

        with patch('ob3.models.requests.post') as mock_post:
            mock_response = type(
                'MockResponse',
                (),
                {
                    'status_code': 200,
                    'text': '{"uri": "test-offer-uri"}',
                    'json': lambda self: {'uri': 'test-offer-uri'},
                },
            )()
            mock_post.return_value = mock_response
            _ = offer_request.call()
            mock_post.assert_called_once()
            _, kwargs = mock_post.call_args
            self.assertEqual(
                kwargs['json'],
                {
                    'credentials': ['test-credential-config-id'],
                    'grants': {'authorization_code': {'issuer_state': badge_instance.entity_id}},
                    'credential_callback': expected_callback_url,
                },
            )

    def test_veramo_offer_request_call_method_error_handling(self):
        """Test that VeramoOfferRequest.call() handles errors correctly."""
        badge_instance = BadgeInstanceMock()
        offer_request = VeramoOfferRequest(
            'test-credential-config-id',
            badge_instance,  # pyright: ignore[reportArgumentType] BK: I could not manage to make a standin for a Django model that inherits or otherwise is compatible to a model
            'http://not-relevant.example.com/',
        )
        offer_request.set_url('http://test-url.com')
        with patch('ob3.models.requests.post') as mock_post:
            mock_response = type('MockResponse', (), {'status_code': 400, 'text': 'mock-error-response'})()
            mock_post.return_value = mock_response

            with self.assertRaises(Exception) as context:
                _ = offer_request.call()

            self.assertIn('Failed to create offer', str(context.exception))
            self.assertIn('400', str(context.exception))
            self.assertIn('mock-error-response', str(context.exception))
