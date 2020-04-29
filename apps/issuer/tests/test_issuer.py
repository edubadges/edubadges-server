import json
from mainsite.tests import BadgrTestCase
from issuer.testfiles.helper import issuer_json, badgeclass_json


class IssuerAPITest(BadgrTestCase):

    def test_create_issuer(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_create=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer_json['faculty'] = faculty.entity_id
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        self.assertEqual(201, response.status_code)

    def test_may_not_create_issuer(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer_json['faculty'] = faculty.entity_id
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        self.assertEqual(400, response.status_code)
        error_message = str(response.data['fields']['instance'][0]['error_message'])
        self.assertEqual(error_message, "You don't have the necessary permissions")

    def test_create_badgeclass(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_create=True)
        badgeclass_json['issuer'] = issuer.entity_id
        response = self.client.post("/issuer/badgeclasses/create",
                                    json.dumps(badgeclass_json), content_type='application/json')
        self.assertEqual(201, response.status_code)

    def test_may_not_create_badgeclass(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_read=True)
        badgeclass_json['issuer'] = issuer.entity_id
        response = self.client.post("/issuer/badgeclasses/create", json.dumps(badgeclass_json), content_type='application/json')
        self.assertEqual(400, response.status_code)
        error_message = str(response.data['fields']['instance'][0]['error_message'])
        self.assertEqual(error_message, "You don't have the necessary permissions")

    def test_delete(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_staff_membership(teacher1, teacher1.institution, may_delete=True)
        badgeclass_response = self.client.delete("/issuer/badgeclasses/edit/{}".format(badgeclass.entity_id),
                                                 content_type='application/json')
        self.assertEqual(badgeclass_response.status_code, 204)
        faculty_response = self.client.delete("/institution/faculties/edit/{}".format(faculty.entity_id),
                                              content_type='application/json')
        self.assertEqual(faculty_response.status_code, 404)
        issuer_response = self.client.delete("/issuer/edit/{}".format(issuer.entity_id),
                                             content_type='application/json')
        self.assertEqual(issuer_response.status_code, 204)
        faculty_response2 = self.client.delete("/institution/faculties/edit/{}".format(faculty.entity_id),
                                              content_type='application/json')
        self.assertEqual(faculty_response2.status_code, 204)
        self.assertTrue(self.instance_is_removed(badgeclass))
        self.assertTrue(self.instance_is_removed(issuer))
        self.assertTrue(self.instance_is_removed(faculty))
        self.assertEqual(teacher1.institution.cached_faculties().__len__(), 0)


    def test_issuer_schema(self):
        pass

    def test_award_valid_badge(self):
        pass

    def test_award_badge_expiration_date(self):
        pass


class IssuerExtensionsTest(BadgrTestCase):

    def test_create_edit_remove_issuer_extensions(self):
        pass

    def test_create_edit_remove_badgeclass_extensions(self):
        pass

    def test_validate_extensions_context(self):
        pass


class IssuerModelsTest(BadgrTestCase):

    def test_recursive_deletion(self):
        """tests removal of entities and subsequent cache updates"""
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        staff = self.setup_staff_membership(teacher1, badgeclass)
        self.assertEqual(teacher1.cached_badgeclass_staffs(), [staff])
        issuer.delete()
        self.assertTrue(self.instance_is_removed(issuer))
        self.assertTrue(self.instance_is_removed(badgeclass))
        self.assertTrue(self.instance_is_removed(staff))
        self.assertEqual(teacher1.cached_badgeclass_staffs().__len__(), 0)
        self.assertEqual(faculty.cached_issuers().__len__(), 0)

