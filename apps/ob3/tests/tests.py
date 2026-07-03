import json
from unittest.mock import Mock, patch

from mainsite.tests import BadgrTestCase

FAKE_ACCESS_TOKEN = "test-access-token"
AUTH_HEADER = {"HTTP_AUTHORIZATION": f"Bearer {FAKE_ACCESS_TOKEN}"}


class Ob3TestCase(BadgrTestCase):
    def _setup_assertion(self):
        teacher = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher)
        return student, assertion


class TestCredentialsView(Ob3TestCase):
    """
    CredentialsView is now a thin client of the ec-issuer administrative API
    (see apps/ob3/openapi.yaml). These tests mock the outbound `requests.post`
    call so no real ec-issuer instance is required.
    """

    URL = "/ob3/v1/ob3"

    @patch("ob3.api.requests.post")
    def test_creates_offer_via_ec_issuer(self, mock_post):
        _, assertion = self._setup_assertion()
        offer_uri = "openid-credential-offer://?credential_offer_uri=http://localhost:8001/offers/1234"
        mock_post.return_value = Mock(
            status_code=201,
            json=Mock(return_value={"uri": offer_uri, "offer_id": "1234"}),
        )

        response = self.client.post(
            self.URL,
            data=json.dumps({"badge_id": assertion.id}),
            content_type="application/json",
            **AUTH_HEADER,
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["offer"], offer_uri)

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        self.assertTrue(kwargs["url"].endswith("/api/v1/offers"))
        self.assertEqual(
            kwargs["json"],
            {"award_id": assertion.entity_id, "access_token": FAKE_ACCESS_TOKEN},
        )
        self.assertTrue(kwargs["headers"]["Authorization"].startswith("Bearer "))
        self.assertEqual(kwargs["timeout"], 5)

    @patch("ob3.api.requests.post")
    def test_unknown_badge_id_returns_404(self, mock_post):
        self.setup_student(authenticate=True)

        response = self.client.post(
            self.URL,
            data=json.dumps({"badge_id": 999999}),
            content_type="application/json",
            **AUTH_HEADER,
        )

        self.assertEqual(response.status_code, 404)
        mock_post.assert_not_called()

    @patch("ob3.api.requests.post")
    def test_badge_owned_by_other_user_returns_404(self, mock_post):
        _, assertion = self._setup_assertion()
        self.setup_student(authenticate=True)  # a different, unrelated student

        response = self.client.post(
            self.URL,
            data=json.dumps({"badge_id": assertion.id}),
            content_type="application/json",
            **AUTH_HEADER,
        )

        self.assertEqual(response.status_code, 404)
        mock_post.assert_not_called()

    @patch("ob3.api.requests.post")
    def test_ec_issuer_error_response_is_propagated_as_bad_request(self, mock_post):
        _, assertion = self._setup_assertion()
        mock_post.return_value = Mock(status_code=502, text="upstream error")

        response = self.client.post(
            self.URL,
            data=json.dumps({"badge_id": assertion.id}),
            content_type="application/json",
            **AUTH_HEADER,
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_bearer_token_returns_bad_request(self):
        _, assertion = self._setup_assertion()

        # Authenticated (force_authenticate), but no Authorization header to forward.
        response = self.client.post(
            self.URL, data=json.dumps({"badge_id": assertion.id}), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_request_is_rejected(self):
        response = self.client.post(self.URL, data=json.dumps({"badge_id": 1}), content_type="application/json")

        self.assertEqual(response.status_code, 401)


class TestCredentialsViewGet(Ob3TestCase):
    """
    CredentialsView.get() is called by ec-issuer (with the access token
    forwarded by CredentialsView.post()) to fetch award data for an award.
    It returns the badge instance's existing OB2.0 JSON representation
    (BadgeInstance.get_json()) with badgeclass and issuer expanded -
    ec-issuer maps this into an OBv3 credential itself, edubadges-server
    doesn't maintain that mapping.
    """

    def _url(self, award_id):
        return f"/ob3/v1/awards/{award_id}"

    def test_owner_can_fetch_award_data(self):
        _, assertion = self._setup_assertion()

        response = self.client.get(self._url(assertion.entity_id), **AUTH_HEADER)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["type"], "Assertion")
        self.assertIn("issuedOn", response.data)
        self.assertEqual(response.data["badge"]["name"], assertion.badgeclass.name)
        self.assertEqual(response.data["badge"]["issuer"]["name"], assertion.badgeclass.issuer.name)
        self.assertTrue(response.data["recipient"]["hashed"])

    def test_non_owner_gets_404(self):
        _, assertion = self._setup_assertion()
        self.setup_student(authenticate=True)  # a different, unrelated student

        response = self.client.get(self._url(assertion.entity_id), **AUTH_HEADER)

        self.assertEqual(response.status_code, 404)

    def test_unknown_award_id_returns_404(self):
        self.setup_student(authenticate=True)

        response = self.client.get(self._url("does-not-exist"), **AUTH_HEADER)

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_request_is_rejected(self):
        _, assertion = self._setup_assertion()
        self.client.force_authenticate(user=None)

        response = self.client.get(self._url(assertion.entity_id), **AUTH_HEADER)

        self.assertEqual(response.status_code, 401)
