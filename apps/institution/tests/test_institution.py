import json

from institution.models import Institution
from institution.testfiles.helper import faculty_json, institution_json
from mainsite.tests import BadgrTestCase


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
        description = 'description'
        institution_json['description'] = description
        response = self.client.put("/institution/edit/{}".format(teacher1.institution.entity_id),
                                   data=json.dumps(institution_json), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        institution = Institution.objects.get(pk=teacher1.institution.pk)
        self.assertEqual(institution.description, description)
        response = self.client.delete("/institution/edit/".format(teacher1.institution.entity_id),
                                      content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_check_institutions_validity(self):
        teacher1 = self.setup_teacher()
        teacher1.institution.identifier
        response = self.client.post("/institution/check", data=json.dumps([teacher1.institution.identifier]),
                                    content_type='application/json')
        self.assertTrue(response.data[0]['valid'])
        response = self.client.post("/institution/check", data=json.dumps(['NOT EXIST']),
                                    content_type='application/json')
        self.assertFalse(response.data[0]['valid'])


class TestInstitutionSchema(BadgrTestCase):

    def test_institution_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        query = 'query foo {institutions {entityId grondslagFormeel grondslagInformeel identifier contentTypeId}}'
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['institutions'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['institutions'][0]['entityId']))
        self.assertTrue(bool(response['data']['institutions'][0]['grondslagFormeel']))
        self.assertTrue(bool(response['data']['institutions'][0]['grondslagInformeel']))

    def test_faculty_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        query = 'query foo {faculties {entityId contentTypeId}}'
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        self.setup_faculty(teacher1.institution)
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['faculties'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['faculties'][0]['entityId']))