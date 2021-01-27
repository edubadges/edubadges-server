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
        response = self.client.put('/earner/badges/{}'.format(assertion.entity_id),
                                   data=json.dumps(body), content_type='application/json')
        self.assertTrue(response.status_code == 200)
        self.assertTrue(student.cached_badgeinstances()[0].public)  # instant cache update

    def test_reject_assertion(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)
        response = self.client.delete('/earner/badges/{}'.format(assertion.entity_id), content_type='application/json')
        self.assertEqual(response.status_code, 204)
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
        query = 'query foo {badgeInstances {entityId}}'
        response = self.graphene_post(student, query)
        self.assertEqual(response['data']['badgeInstances'].__len__(), 3)

    def test_share_assertion(self):
        pass