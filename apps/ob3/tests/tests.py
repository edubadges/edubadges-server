import json
from unittest.mock import Mock, patch

from mainsite.tests import BadgrTestCase


class TestCredentialsView(BadgrTestCase):
    """
    CredentialsView is now a thin client of the ec-issuer administrative API
    (see apps/ob3/openapi.yaml). These tests mock the outbound `requests.post`
    call so no real ec-issuer instance is required.
    """

    URL = "/ob3/v1/ob3"

    def _setup_assertion(self):
        teacher = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher)
        return student, assertion

    @patch("ob3.api.requests.post")
    def test_creates_offer_via_ec_issuer(self, mock_post):
        _, assertion = self._setup_assertion()
        offer_uri = "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/1234"
        mock_post.return_value = Mock(
            status_code=201,
            json=Mock(return_value={"uri": offer_uri, "offer_id": "1234"}),
        )

        response = self.client.post(
            self.URL, data=json.dumps({"badge_id": assertion.id}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["offer"], offer_uri)

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertTrue(kwargs["url"].endswith("/api/v1/offers"))
        self.assertEqual(kwargs["json"], {"award_id": assertion.entity_id})
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Bearer "))
        self.assertEqual(kwargs["timeout"], 5)

    @patch("ob3.api.requests.post")
    def test_unknown_badge_id_returns_404(self, mock_post):
        self.setup_student(authenticate=True)

        response = self.client.post(self.URL, data=json.dumps({"badge_id": 999999}), content_type="application/json")

        self.assertEqual(response.status_code, 404)
        mock_post.assert_not_called()

    @patch("ob3.api.requests.post")
    def test_badge_owned_by_other_user_returns_404(self, mock_post):
        _, assertion = self._setup_assertion()
        self.setup_student(authenticate=True)  # a different, unrelated student

        response = self.client.post(
            self.URL, data=json.dumps({"badge_id": assertion.id}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 404)
        mock_post.assert_not_called()

    @patch("ob3.api.requests.post")
    def test_ec_issuer_error_response_is_propagated_as_bad_request(self, mock_post):
        _, assertion = self._setup_assertion()
        mock_post.return_value = Mock(status_code=502, text="upstream error")

        response = self.client.post(
            self.URL, data=json.dumps({"badge_id": assertion.id}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
