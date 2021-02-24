import json
from django.db import IntegrityError

from institution.models import Institution
from institution.testfiles.helper import faculty_json, institution_json
from mainsite.tests import BadgrTestCase
from mainsite.exceptions import BadgrValidationFieldError


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
        institution_json['description_english'] = description
        institution_json['description_dutch'] = description
        response = self.client.put("/institution/edit/{}".format(teacher1.institution.entity_id),
                                   data=json.dumps(institution_json), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        institution = Institution.objects.get(pk=teacher1.institution.pk)
        self.assertEqual(institution.description_english, description)
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

    def test_faculty_delete(self):
        """Test recursive faculty deletion"""
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_delete=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student,
                                         badgeclass=badgeclass,
                                         created_by=teacher1)
        response_fail = self.client.delete("/issuer/faculty/delete/{}".format(faculty.entity_id),
                                                 content_type='application/json')
        self.assertEqual(response_fail.status_code, 404)
        assertion.delete()
        response_success = self.client.delete("/institution/faculties/delete/{}".format(faculty.entity_id),
                                      content_type='application/json')
        self.assertEqual(response_success.status_code, 204)
        self.assertTrue(self.instance_is_removed(faculty))
        self.assertTrue(self.instance_is_removed(issuer))
        self.assertTrue(self.instance_is_removed(badgeclass))
        self.assertEqual(teacher1.institution.cached_faculties().__len__(), 0)


class InstitutionModelsTest(BadgrTestCase):

    def test_faculty_uniqueness_constraints_when_archiving(self):
        """Checks if uniquness constraints on name dont trigger for archived Faculties"""
        teacher1 = self.setup_teacher(authenticate=True)
        setup_faculty_kwargs = {'institution': teacher1.institution, 'name_english': 'The same'}
        faculty = self.setup_faculty(**setup_faculty_kwargs)
        self.assertRaises(BadgrValidationFieldError, self.setup_faculty, **setup_faculty_kwargs)
        setup_faculty_kwargs['archived'] = True
        self.setup_faculty(**setup_faculty_kwargs)
        faculty.archive()


class TestInstitutionSchema(BadgrTestCase):

    def test_institution_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        query = 'query foo {institutions {entityId grondslagFormeel grondslagInformeel identifier contentTypeId, defaultLanguage}}'
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['institutions'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['institutions'][0]['entityId']))
        self.assertTrue(bool(response['data']['institutions'][0]['grondslagFormeel']))
        self.assertTrue(bool(response['data']['institutions'][0]['grondslagInformeel']))
        self.assertTrue(bool(response['data']['institutions'][0]['defaultLanguage']))

    def test_faculty_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        query = 'query foo {faculties {entityId contentTypeId}}'
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        self.setup_faculty(institution=teacher1.institution)
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['faculties'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['faculties'][0]['entityId']))