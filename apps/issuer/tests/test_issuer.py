import os
import json
from issuer.models import Issuer
from issuer.testfiles.helper import issuer_json, badgeclass_json
from mainsite.tests import BadgrTestCase
from django.urls import reverse


class IssuerAPITest(BadgrTestCase):

    def test_create_issuer(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_create=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer_json['faculty'] = faculty.entity_id
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        self.assertEqual(201, response.status_code)
        del issuer_json['image']
        issuer_json['name'] = 'other_name'
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        created_no_image_issuer = Issuer.objects.get(entity_id=response.data['entity_id'])
        self.assertEqual(response.data['image'], created_no_image_issuer.institution.image_url())

    def test_may_not_create_issuer(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer_json['faculty'] = faculty.entity_id
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        self.assertEqual(400, response.status_code)
        self.assertEqual(str(response.data['fields']['error_message']), "You don't have the necessary permissions")

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
        self.assertEqual(str(response.data['fields']['error_message']), "You don't have the necessary permissions")

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

    def test_enroll_and_award_badge(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True, affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True, may_read=True)
        enroll_body = {"badgeclass_slug": badgeclass.entity_id}
        terms = badgeclass._get_terms()
        accept_terms_body = [{'terms_entity_id': terms.entity_id, 'accepted': True}]
        terms_accept_response = self.client.post("/v1/user/terms/accept", json.dumps(accept_terms_body),
                                                 content_type='application/json')
        enrollment_response = self.client.post("/lti_edu/enroll", json.dumps(enroll_body),
                                               content_type='application/json')
        self.assertEqual(enrollment_response.status_code, 201)
        self.client.logout()
        self.authenticate(teacher1)
        award_body = {"issue_signed": False, "create_notification": True,
                      "enrollments": [{"enrollment_entity_id": enrollment_response.data['entity_id']}]}
        award_response = self.client.post('/issuer/badgeclasses/award-enrollments/{}'.format(badgeclass.entity_id),
                                          json.dumps(award_body), content_type='application/json')
        # self.assertTrue(bool(award_response.data[0]['extensions']['extensions:recipientProfile']['name']))
        self.assertEqual(len(student.cached_badgeinstances()), 1)  # test cache update
        self.assertEqual(len(badgeclass.cached_assertions()), 1)  # test cache update
        self.assertEqual(award_response.status_code, 201)

    def test_enrollment_denial(self):
        teacher1 = self.setup_teacher(authenticate=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True, may_read=True,
                                    may_create=True, may_update=True)
        enrollment = self.enroll_user(student, badgeclass)
        response = self.client.put(reverse('api_lti_edu_update_enrollment', kwargs={'entity_id': enrollment.entity_id}))
        self.assertEqual(response.status_code, 200)

    def test_award_badge_expiration_date(self):
        pass

    def test_assertion_image_privacy(self):
        teacher1 = self.setup_teacher()
        outside_teacher = self.setup_teacher()
        student = self.setup_student()
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(student, badgeclass, teacher1)
        response = self.client.get('/media/uploads/badges/{}'.format(os.path.basename(assertion.image.path)))
        self.assertEqual(response.status_code, 403)
        self.authenticate(outside_teacher)
        response = self.client.get('/media/uploads/badges/{}'.format(os.path.basename(assertion.image.path)))
        self.assertEqual(response.status_code, 403)
        self.authenticate(teacher1)
        response = self.client.get('/media/uploads/badges/{}'.format(os.path.basename(assertion.image.path)))
        self.assertEqual(response.status_code, 200)  # teacher belongs to assertion institution
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        response = self.client.get('/media/uploads/badges/{}'.format(os.path.basename(assertion.image.path)))
        self.assertEqual(response.status_code, 200)
        assertion.public = True
        assertion.save()
        self.client.logout()
        response = self.client.get('/media/uploads/badges/{}'.format(os.path.basename(assertion.image.path)))
        self.assertEqual(response.status_code, 200)


class IssuerPublicAPITest(BadgrTestCase):

    def test_get_name_from_recipient_identifer(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student()
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(teacher1, faculty)
        badgeclas = self.setup_badgeclass(issuer)
        assertion = self.setup_assertion(student, badgeclas, teacher1)
        eduid_hash = assertion.get_json()['recipient']['identity']
        salt = assertion.get_json()['recipient']['salt']
        response = self.client.get('/public/assertions/identity/{}/{}'.format(eduid_hash, salt))
        self.assertEqual(response.status_code, 404)
        assertion.public = True
        assertion.save()
        response = self.client.get('/public/assertions/identity/{}/{}'.format(eduid_hash, salt))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['name'], assertion.get_recipient_name())

# class IssuerExtensionsTest(BadgrTestCase):
#
#     TODO: this test cannot run, because you cannot verify extensions as their @context is hosted on the same machine
#     def test_create_edit_remove_issuer_extensions(self):
#         teacher1 = self.setup_teacher(authenticate=True)
#         self.setup_staff_membership(teacher1, teacher1.institution, may_create=True, may_read=True, may_update=True)
#         faculty = self.setup_faculty(institution=teacher1.institution)
#         issuer_json['faculty'] = faculty.entity_id
#         response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
#         issuer = Issuer.objects.get(entity_id=response.data['entity_id'])
#         self.assertEqual(issuer.extension_items.__len__(), 1)
#         extensions = issuer_json.pop('extensions')
#         issuer_json['extensions'] = {}
#         response = self.client.put('/issuer/edit/{}'.format(issuer.entity_id), json.dumps(issuer_json), content_type='application/json')
#         self.assertEqual(issuer.extension_items.__len__(), 0)
#         issuer_json['extensions'] = extensions
#         response = self.client.put('/issuer/edit/{}'.format(issuer.entity_id), json.dumps(issuer_json), content_type='application/json')
#         self.assertEqual(issuer.extension_items.__len__(), 1)
#
#     TODO: this test cannot run, because you cannot verify extensions as their @context is hosted on the same machine
#     def test_create_edit_remove_badgeclass_extensions(self):
#         teacher1 = self.setup_teacher(authenticate=True)
#         self.setup_staff_membership(teacher1, teacher1.institution, may_create=True, may_read=True, may_update=True)
#         faculty = self.setup_faculty(institution=teacher1.institution)
#         issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
#         badgeclass_json['issuer'] = issuer.entity_id
#         response = self.client.post('/issuer/badgeclasses/create', json.dumps(badgeclass_json), content_type='application/json')
#         badgeclass = BadgeClass.objects.get(entity_id=response.data['entity_id'])
#         self.assertEqual(badgeclass.extension_items.__len__(), 2)
#         ects_extension = badgeclass_json['extensions'].pop('extensions:ECTSExtension')
#         response = self.client.put('/issuer/badgeclasses/edit/{}'.format(badgeclass.entity_id), json.dumps(badgeclass_json), content_type='application/json')
#         self.assertEqual(badgeclass.extension_items.__len__(), 1)
#         badgeclass_json['extensions']['extensions:ECTSExtension'] = ects_extension
#         response = self.client.put('/issuer/badgeclasses/edit/{}'.format(badgeclass.entity_id), json.dumps(badgeclass_json), content_type='application/json')
#         self.assertEqual(badgeclass.extension_items.__len__(), 2)
#
#     def test_institution_vars_end_up_in_issuer_json_as_extensions(self):
#         pass


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


class IssuerSchemaTest(BadgrTestCase):

    def test_issuer_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(teacher1.institution)
        self.setup_issuer(teacher1, faculty)
        query = 'query foo {issuers {entityId contentTypeId}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['issuers'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['issuers'][0]['entityId']))

    def test_badgeclass_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(teacher1.institution)
        issuer = self.setup_issuer(teacher1, faculty)
        self.setup_badgeclass(issuer)
        query = 'query foo {badgeClasses {entityId contentTypeId terms {entityId termsUrl {url excerpt language}}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['badgeClasses'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['badgeClasses'][0]['entityId']))
        self.assertTrue(bool(response['data']['badgeClasses'][0]['terms']['termsUrl'][0]['language']))
        self.assertEqual(len(response['data']['badgeClasses'][0]['terms']['termsUrl']), 4)
