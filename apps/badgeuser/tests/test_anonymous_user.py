"""
Regression tests: unauthenticated (AnonymousUser) requests must not crash the
GraphQL resolvers. Previously `currentUser` raised
"Received incompatible instance 'AnonymousUser'" and `enrollment` raised
"Field 'id' expected a number but got <SimpleLazyObject: ...AnonymousUser...>".
"""

from django.contrib.auth.models import AnonymousUser
from lti_edu.models import StudentsEnrolled
from mainsite.tests import BadgrTestCase


class AnonymousUserQueriesTest(BadgrTestCase):
    def test_current_user_anonymous_returns_null(self):
        result = self.graphene_post(AnonymousUser(), "query { currentUser { entityId } }")
        self.assertFalse(result.get("errors"))
        self.assertIsNone(result["data"]["currentUser"])

    def test_enrollments_anonymous_returns_empty_list(self):
        result = self.graphene_post(AnonymousUser(), "query { enrollments { entityId } }")
        self.assertFalse(result.get("errors"))
        self.assertEqual(result["data"]["enrollments"], [])

    def test_enrollment_anonymous_returns_null(self):
        result = self.graphene_post(AnonymousUser(), 'query { enrollment(id: "some-entity-id") { entityId } }')
        self.assertFalse(result.get("errors"))
        self.assertIsNone(result["data"]["enrollment"])

    def test_enrollment_authenticated_still_returns_own(self):
        teacher = self.setup_teacher(authenticate=True)
        badgeclass = self.setup_badgeclass(self.setup_issuer(teacher))
        student = self.setup_student()
        enrollment = StudentsEnrolled.objects.create(user=student, badge_class=badgeclass)
        query = f'query {{ enrollment(id: "{enrollment.entity_id}") {{ entityId }} }}'
        result = self.graphene_post(student, query)
        self.assertFalse(result.get("errors"))
        self.assertEqual(result["data"]["enrollment"]["entityId"], enrollment.entity_id)
