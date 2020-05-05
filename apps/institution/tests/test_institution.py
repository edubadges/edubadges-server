import json
from mainsite.tests import BadgrTestCase
from institution.testfiles.helper import faculty_json, institution_json


class InstitutionTest(BadgrTestCase):

    def test_create_faculty(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_create=True)
        response = self.client.post("/institution/faculties/create", data=json.dumps(faculty_json),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 201)

    def test_edit_institution(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_create=True, may_update=True)
        institution_json['name'] = 'NewName'
        response = self.client.put("/institution/edit/{}".format(teacher1.institution.entity_id),
                                    data=json.dumps(institution_json), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(teacher1.institution.name, 'NewName')
        response = self.client.delete("/institution/edit/".format(teacher1.institution.entity_id),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 404)


    def test_institution_schema(self):
        pass
