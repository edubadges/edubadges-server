import json

from http import HTTPStatus

from issuer.models import BadgeClassExtension, IssuerExtension
from mainsite.tests import BadgrTestCase


class BackpackAPITest(BadgrTestCase):
    def test_make_assertion_public(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)
        self.assertTrue(not assertion.public)
        body = {"public": True}  # make_assertion_public_private
        response = self.client.put(
            f"/earner/badges/{assertion.entity_id}", data=json.dumps(body), content_type="application/json"
        )
        self.assertTrue(response.status_code == HTTPStatus.OK)  # type: ignore[attr-defined]
        self.assertTrue(student.cached_badgeinstances()[0].public)  # instant cache update

    def test_reject_assertion(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)
        response = self.client.delete(f"/earner/badges/{assertion.entity_id}", content_type="application/json")
        self.assertEqual(response.status_code, 204)  # type: ignore[attr-defined]
        cached_assertion = student.cached_badgeinstances()[0]
        self.assertEqual(cached_assertion.acceptance, cached_assertion.ACCEPTANCE_REJECTED)

    def test_get_assertions_graphql(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        ass1 = self.setup_assertion(student, badgeclass, teacher1)  # noqa: F841
        ass2 = self.setup_assertion(student, badgeclass, teacher1)  # noqa: F841
        ass3 = self.setup_assertion(student, badgeclass, teacher1)  # noqa: F841
        query = "query foo {badgeInstances {entityId}}"
        response = self.graphene_post(student, query)
        self.assertEqual(response["data"]["badgeInstances"].__len__(), 3)  # type: ignore[union-attr]

    def test_award_detail_includes_all_properties(self):
        teacher1 = self.setup_teacher(first_name="Jane", last_name="Doe")
        student = self.setup_student(
            first_name="John",
            last_name="Smith",
            authenticate=True,
            email="john.smith@example.com",
        )
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)

        response = self.client.get(
            f"/earner/awards/{assertion.entity_id}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)  # type: ignore[attr-defined]
        data = response.json()  # type: ignore[attr-defined]

        # User fields
        self.assertEqual(data["given_name"], "John")
        self.assertEqual(data["family_name"], "Smith")
        self.assertEqual(data["email"], "john.smith@example.com")

        # Core badge instance fields
        self.assertEqual(data["id"], f"http://localhost:8000/public/assertions/{assertion.entity_id}")
        self.assertIsInstance(data["created_at"], str)
        self.assertIsInstance(data["issued_on"], str)
        self.assertEqual(data["award_type"], "requested")
        self.assertFalse(data["revoked"])
        self.assertIsNone(data["expires_at"])
        self.assertEqual(data["acceptance"], "Unaccepted")
        self.assertFalse(data["public"])
        self.assertFalse(data["include_grade_achieved"])
        self.assertIsNone(data["revocation_reason"])
        self.assertIsInstance(data["evidences"], list)
        self.assertEqual(data["evidences"], [])

        # badgeclass nested object
        self.assertIsInstance(data["badgeclass"], dict)
        self.assertEqual(data["badgeclass"]["id"], f"http://localhost:8000/public/badges/{badgeclass.entity_id}")
        self.assertEqual(data["badgeclass"]["name"], badgeclass.name)
        self.assertIsInstance(data["badgeclass"]["issuer"], dict)
        self.assertEqual(data["badgeclass"]["issuer"]["id"], f"http://localhost:8000/public/issuers/{issuer.entity_id}")

        # badgeclass: criteria (nested)
        self.assertIsInstance(data["badgeclass"]["criteria"], dict)
        self.assertEqual(data["badgeclass"]["criteria"]["narrative"], badgeclass.criteria_text)

        # badgeclass: assessment & participation fields
        self.assertIsNone(data["badgeclass"]["participation"])
        self.assertIsNone(data["badgeclass"]["assessment_type"])
        self.assertFalse(data["badgeclass"]["assessment_id_verified"])
        self.assertFalse(data["badgeclass"]["assessment_supervised"])

    def test_extension_flattening_with_valid_data(self):
        """Verify badgeclass and issuer extensions are flattened as flat keys."""
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)

        # Create a valid badgeclass extension
        BadgeClassExtension.objects.update_or_create(
            badgeclass=badgeclass,
            name="EQF",
            defaults={
                "original_json": json.dumps({"type": ["Extension", "extensions:EQFExtension"], "EQF": 7}),
            },
        )

        # Create a valid issuer extension
        IssuerExtension.objects.update_or_create(
            issuer=issuer,
            name="Type",
            defaults={
                "original_json": json.dumps(
                    {"type": ["Extension", "extensions:TypeExtension"], "Type": "organization"}
                ),
            },
        )

        response = self.client.get(
            f"/earner/awards/{assertion.entity_id}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["badgeclass"]["EQF"], 7)
        self.assertEqual(data["badgeclass"]["issuer"]["Type"], "organization")

    def test_extension_flattening_with_malformed_data(self):
        """Verify malformed extensions don't crash the endpoint."""
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)

        # Create extensions with bad data
        BadgeClassExtension.objects.update_or_create(
            badgeclass=badgeclass,
            name="BadExtension",
            defaults={"original_json": None},
        )
        BadgeClassExtension.objects.update_or_create(
            badgeclass=badgeclass,
            name="MalformedExtension",
            defaults={"original_json": "not json"},
        )
        IssuerExtension.objects.update_or_create(
            issuer=issuer,
            name="BadIssuerExt",
            defaults={"original_json": ""},
        )

        response = self.client.get(
            f"/earner/awards/{assertion.entity_id}",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # The flat keys should NOT appear (extensions were skipped gracefully)
        self.assertNotIn("BadExtension", data["badgeclass"])
        self.assertNotIn("MalformedExtension", data["badgeclass"])
