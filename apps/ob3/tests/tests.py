from typing import List, Optional
from django.test import SimpleTestCase

from datetime import datetime as DateTime

from ob3.models import ImpierceOfferRequest as OfferRequest, IdentityObject
from ob3.serializers import ImpierceOfferRequestSerializer as OfferRequestSerializer

from mainsite.settings import UI_URL

class BadgeClassMock:
    def __init__(self):
        self.criteria_text = "You must Lorem Ipsum, **dolor** _sit_ amet"
        self.description = "This badge is a Lorem Ipsum, **dolor** _sit_ amet"
        self.name = "Mock Badge"
        self.issuer = IssuerMock()
        self.participation: Optional[str] = None
        self.alignment_items: List[AligmentItemMock] = []
        self.extension_items = {}

    def image_url(self):
        return "https://example.com/images/mock.png"

class BadgeInstanceMock:
    def __init__(self):
        self.entity_id = "BADGE1234"
        self.salt: Optional[str] = None
        self.recipient_identifier: Optional[str] = None

        self.badgeclass = BadgeClassMock()
        self.issued_on: Optional[DateTime] = None
        self.expires_at: Optional[DateTime] = None

class IssuerMock:
    def __init__(self):
        self.id = "ISS1234"
        self.name = "Mock Issuer"

class AligmentItemMock:
    def __init__(self):
        self.target_name = "interne geneeskunde"
        self.target_url = "https://example.com/esco/1337"
        self.target_code = "1337"
        self.target_framework = "ESCO"
        self.target_description = "# example cool"

def mock_hasher(_id, _salt):
   return "mock_hash"

class TestCredentialsSerializers(SimpleTestCase):
    def test_serializer_serializes_credential(self):
        badge_instance = BadgeInstanceMock()
        actual_data = self._serialize_it(badge_instance)
        expected_data = {
            "offerId": "offer_id",
            "expiresAt": "never",
            "credentialConfigurationId": "credential_configuration_id",
            "credential": {
                "id": f"{UI_URL}/public/assertions/BADGE1234",
                "issuer": {
                    "id": f"{UI_URL}/ob3/issuers/ISS1234",
                    "type": ["Profile"],
                    "name": "Mock Issuer"
                },
                "credentialSubject": {
                    "type": ["AchievementSubject"],
                    "achievement": {
                        "id": f"{UI_URL}/public/assertions/BADGE1234",
                        "type": ["Achievement"],
                        "criteria": {
                            "narrative": "You must Lorem Ipsum, **dolor** _sit_ amet"
                        },
                        "description": "This badge is a Lorem Ipsum, **dolor** _sit_ amet",
                        "name": "Mock Badge",
                        "image": {
                            "type": "Image",
                            "id": "https://example.com/images/mock.png"
                        }
                    }
                }
            }
        }

        self.maxDiff = None # Debug full diff
        self.assertDictEqual(actual_data, expected_data)

    def test_recipient(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.recipient_identifier = "1234abc123abc"
        badge_instance.salt = "s@lt"
        actual_data = self._serialize_it(badge_instance)
        expected_identifier = {
            "type": "IdentityObject",
            "hashed": True,
            "identityHash": "sha256$a2441d313d3d31514464ed6732d255df3391cbc85dd374d8a94b683248dcb7b8",
            "identityType": "emailAddress",
            "salt": "s@lt",
        }
        self.assertEqual(len(actual_data["credential"]["credentialSubject"]["identifier"]), 1)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["identifier"][0], expected_identifier)

    def test_optional_valid_from_field_set(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.issued_on = DateTime.fromisoformat("2020-01-01:01:13:37")
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data["credential"]["validFrom"], "2020-01-01T01:13:37Z")

    def test_optional_valid_from_field_notset(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.issued_on = None
        actual_data = self._serialize_it(badge_instance)

        self.assertNotIn("validFrom", actual_data)

    def test_optional_valid_until(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = DateTime.fromisoformat("2020-01-01:01:13:37")
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data["credential"]["validUntil"], "2020-01-01T01:13:37Z")

    def test_impierce_offer_request_expires_at(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = DateTime.fromisoformat("2020-01-01:01:13:37")
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data["expiresAt"], "2020-01-01T01:13:37Z")

    def test_impierce_offer_request_expires_at_notset(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.expires_at = None
        actual_data = self._serialize_it(badge_instance)

        self.assertEqual(actual_data["expiresAt"], "never")

    def test_education_language_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:LanguageExtension": { "Language": "en_EN" }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["inLanguage"], "en_EN")

    def test_ects_extension_int(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:ECTSExtension": { "ECTS": int(1) }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["ECTS"], 1.0)

    def test_ects_extension_float(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:ECTSExtension": { "ECTS": float(2.5) }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["ECTS"], 2.5)

    def test_ects_extension_one_place(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:ECTSExtension": { "ECTS": float(2.54321) }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["ECTS"], 2.5)

    def test_ects_extension_max_999(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:ECTSExtension": { "ECTS": float(240.0) }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["ECTS"], 240)

    def test_education_program_identifier_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:EducationProgramIdentifierExtension": { "EducationProgramIdentifier": "1234" }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["educationProgramIdentifier"], "1234")

    def test_participation_type(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.participation = "blended"

        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["participationType"], "blended")

    def test_aligments(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.alignment_items = [AligmentItemMock()]
        actual_data = self._serialize_it(badge_instance)
        actual_data = actual_data["credential"]["credentialSubject"]["achievement"]
        expected_alignment = {
            "type": ["Alignment"],
            "targetType": "ext:ESCOAlignment",
            "targetName": "interne geneeskunde",
            "targetDescription":"# example cool",
            "targetUrl":"https://example.com/esco/1337",
            "targetCode":"1337",
        }

        self.assertIn(expected_alignment, actual_data["alignment"])

    def _serialize_it(self, badge_instance: BadgeInstanceMock):
       # TODO: We should test both impierce and sphereon models and serializers
       edu_credential = OfferRequest("offer_id", "credential_configuration_id", badge_instance)
       return dict(OfferRequestSerializer(edu_credential).data)

class TestCredentialModels(SimpleTestCase):
    def test_identity_object_adds_identity_hash_from_hasher(self):
        subject = IdentityObject("1234abc123abc", "s@lt", hasher=mock_hasher)
        self.assertEqual(subject.identity_hash, "mock_hash")

    def test_identity_object_adds_algorithm_identifier(self):
        subject = IdentityObject("1234abc123abc", "s@lt")
        self.assertTrue(subject.identity_hash.startswith("sha256$"))

    def test_identity_object_adds_salt(self):
        subject_one = IdentityObject("1234abc123abc", "1")
        subject_two = IdentityObject("1234abc123abc", "2")
        self.assertNotEqual(subject_one.identity_hash, subject_two.identity_hash)

    def test_identity_object_ignores_case_in_recipient_identifier(self):
        subject_lower = IdentityObject("1234abc123abc", "s@lt")
        subject_upper = IdentityObject("1234ABC123ABC", "s@lt")
        self.assertEqual(subject_lower.identity_hash, subject_upper.identity_hash)
