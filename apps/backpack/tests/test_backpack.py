import json

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
            "/earner/badges/{}".format(assertion.entity_id), data=json.dumps(body), content_type="application/json"
        )
        self.assertTrue(response.status_code == 200)  # type: ignore[attr-defined]
        self.assertTrue(student.cached_badgeinstances()[0].public)  # instant cache update

    def test_reject_assertion(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)
        response = self.client.delete("/earner/badges/{}".format(assertion.entity_id), content_type="application/json")
        self.assertEqual(response.status_code, 204)  # type: ignore[attr-defined]
        cached_assertion = student.cached_badgeinstances()[0]
        self.assertEqual(cached_assertion.acceptance, cached_assertion.ACCEPTANCE_REJECTED)

    def test_get_assertions_graphql(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        ass1 = self.setup_assertion(student, badgeclass, teacher1)
        ass2 = self.setup_assertion(student, badgeclass, teacher1)
        ass3 = self.setup_assertion(student, badgeclass, teacher1)
        query = "query foo {badgeInstances {entityId}}"
        response = self.graphene_post(student, query)
        self.assertEqual(response["data"]["badgeInstances"].__len__(), 3)  # type: ignore[union-attr]

    def test_award_detail_includes_user_info(self):
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
            "/earner/badges/{}".format(assertion.entity_id),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)  # type: ignore[attr-defined]
        data = response.json()  # type: ignore[attr-defined]
        self.assertEqual(data["given_name"], "John")
        self.assertEqual(data["family_name"], "Smith")
        self.assertEqual(data["email"], "john.smith@example.com")

        # Core badge instance fields
        self.assertEqual(data["id"], assertion.id)
        self.assertEqual(data["entity_id"], assertion.entity_id)
        self.assertIsInstance(data["created_at"], str)
        self.assertIsInstance(data["issued_on"], str)
        self.assertEqual(data["award_type"], "requested")
        self.assertFalse(data["revoked"])
        self.assertIsNone(data["expires_at"])
        self.assertEqual(data["acceptance"], "Accepted")
        self.assertFalse(data["public"])
        self.assertFalse(data["include_grade_achieved"])
        self.assertIsNone(data["grade_achieved"])

        # badgeclass nested object
        self.assertIsInstance(data["badgeclass"], dict)
        self.assertEqual(data["badgeclass"]["id"], badgeclass.id)
        self.assertEqual(data["badgeclass"]["entity_id"], badgeclass.entity_id)
        self.assertEqual(data["badgeclass"]["name"], badgeclass.name)
        self.assertIsInstance(data["badgeclass"]["issuer"], dict)
        self.assertEqual(data["badgeclass"]["issuer"]["id"], issuer.id)
