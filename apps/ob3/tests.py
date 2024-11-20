from typing import Optional
from django.test import SimpleTestCase

from datetime import datetime as DateTime

from .models import EduCredential
from .serializers import EduCredentialSerializer

from  mainsite.settings import UI_URL

class BadgeClassMock:
    def __init__(self):
        self.criteria_text = "You must Lorem Ipsum, **dolor** _sit_ amet"
        self.description = "This badge is a Lorem Ipsum, **dolor** _sit_ amet"
        self.name = "Mock Badge"
        self.issuer = IssuerMock()
        self.extension_items = {}

    def image_url(self):
        return "https://example.com/images/mock.png"

class BadgeInstanceMock:
    def __init__(self):
        self.entity_id = "BADGE1234"
        self.badgeclass = BadgeClassMock()
        self.issued_on: Optional[DateTime] = None
        self.expires_at: Optional[DateTime] = None

class IssuerMock:
    def __init__(self):
        self.id = "ISS1234"
        self.name = "Mock Issuer"

class TestCredentialsSerializers(SimpleTestCase):
    def test_serializer_serializes_credential(self):
        badge_instance = BadgeInstanceMock()
        actual_data = self._serialize_it(badge_instance)

        expected_data = {
            "offerId": "offer_id",
            "credentialConfigurationId": "credential_configuration_id",
            "credential": {
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

    def test_education_language_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:LanguageExtension": { "Language": "en_EN" }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["inLanguage"], "en_EN")

    def test_studyload_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:ECTSExtension": { "ECTS": 2.5 }
                }
        actual_data = self._serialize_it(badge_instance)
        # It must be serialized as a Number, not a string
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["ECTS"], 2.5)

    def test_education_program_identifier_extension(self):
        badge_instance = BadgeInstanceMock()
        badge_instance.badgeclass.extension_items = {
                "extensions:EducationProgramIdentifierExtension": { "EducationProgramIdentifier": "1234" }
                }
        actual_data = self._serialize_it(badge_instance)
        self.assertEqual(actual_data["credential"]["credentialSubject"]["achievement"]["educationProgramIdentifier"], "1234")

    def _serialize_it(self, badge_instance: BadgeInstanceMock):
       edu_credential = EduCredential("offer_id", "credential_configuration_id", badge_instance)
       return dict(EduCredentialSerializer(edu_credential).data)
