from django.test import SimpleTestCase

from .models import EduCredential
from .serializers import EduCredentialSerializer

from  mainsite.settings import UI_URL

class BadgeClassMock:
    def __init__(self):
        self.criteria_text = "You must Lorem Ipsum, **dolor** _sit_ amet"
        self.description = "This badge is a Lorem Ipsum, **dolor** _sit_ amet"
        self.name = "Mock Badge"
        self.issuer = IssuerMock()

    def image_url(self):
        return "https://example.com/images/mock.png"

class BadgeInstanceMock:
    def __init__(self):
        self.entity_id = "BADGE1234"
        self.badgeclass = BadgeClassMock()

class IssuerMock:
    def __init__(self):
        self.id = "ISS1234"
        self.name = "Mock Issuer"

class TestCredentialsView(SimpleTestCase):
    def test_serializer_serializes_credential(self):
        badge_instance = BadgeInstanceMock()
        edu_credential = EduCredential("offer_id", "credential_configuration_id", badge_instance)
        serializer = EduCredentialSerializer(edu_credential)
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

        actual_data = dict(serializer.data)
        self.maxDiff = None # Debug full diff
        self.assertDictEqual(actual_data, expected_data)
