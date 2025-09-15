import copy
import json
import os

from directaward.models import DirectAward
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.urls import reverse
from institution.models import Institution
from issuer.models import Issuer
from issuer.testfiles.helper import badgeclass_json, issuer_json
from mainsite.exceptions import BadgrValidationFieldError, BadgrValidationMultipleFieldError
from mainsite.tests import BadgrTestCase


class IssuerAPITest(BadgrTestCase):
    def test_assertion_revoking(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher1)
        post_data = {'revocation_reason': 'revocation_reason', 'assertions': [{'entity_id': assertion.entity_id}]}
        response = self.client.post('/issuer/revoke-assertions', json.dumps(post_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)

    def test_create_issuer(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_create=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer_json['faculty'] = faculty.entity_id
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        self.assertEqual(201, response.status_code)
        del issuer_json['image_english']
        del issuer_json['image_dutch']
        issuer_json['name_english'] = 'other_name'
        issuer_json['name_dutch'] = 'andere_naam'
        response = self.client.post('/issuer/create', json.dumps(issuer_json), content_type='application/json')
        created_no_image_issuer = Issuer.objects.get(entity_id=response.data['entity_id'])
        self.assertEqual(response.data['image_english'], created_no_image_issuer.institution.image_url())

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
        badgeclass_json_copy = copy.deepcopy(badgeclass_json)
        badgeclass_json_copy['issuer'] = issuer.entity_id
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(201, response.status_code)

    def test_create_badgeclass_alignments(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_create=True)
        badgeclass_json_copy = copy.deepcopy(badgeclass_json)
        badgeclass_json_copy['issuer'] = issuer.entity_id
        alignment_json = [
            {
                'target_name': 'name',
                'target_url': 'http://www.google.com',
                'target_description': 'descr',
                'target_framework': 'framework',
                'target_code': 'code',
            }
        ]
        badgeclass_json_copy['alignments'] = alignment_json
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(201, response.status_code)

    def test_create_badgeclass_grondslag_failure(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher1.institution.grondslag_formeel = None
        teacher1.institution.save()
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_create=True)
        badgeclass_json_copy = copy.deepcopy(badgeclass_json)
        badgeclass_json_copy['formal'] = True
        badgeclass_json_copy['issuer'] = issuer.entity_id
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual('215', str(response.data['fields']['error_code']))
        badgeclass_json_copy['formal'] = False
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(201, response.status_code)
        teacher1.institution.grondslag_formeel = Institution.GRONDSLAG_GERECHTVAARDIGD_BELANG
        teacher1.institution.grondslag_informeel = None
        teacher1.institution.save()
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual('216', str(response.data['fields']['error_code']))
        badgeclass_json_copy['formal'] = True
        badgeclass_json_copy['name'] = 'And now for something completely different'
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(201, response.status_code)

    def test_create_badgeclass_image_too_large(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_create=True)
        badgeclass_json_copy = copy.deepcopy(badgeclass_json)
        badgeclass_json_copy['issuer'] = issuer.entity_id
        image_path = self.get_test_image_path_too_large()
        image_base64 = self.get_image_data(image_path)
        badgeclass_json_copy['image'] = image_base64
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(400, response.status_code)
        self.assertTrue(bool(str(response.data['fields']['error_message']['image'][0]['error_message'])))

    def test_may_not_create_badgeclass(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, issuer, may_read=True)
        badgeclass_json_copy = copy.deepcopy(badgeclass_json)
        badgeclass_json_copy['issuer'] = issuer.entity_id
        response = self.client.post(
            '/issuer/badgeclasses/create', json.dumps(badgeclass_json_copy), content_type='application/json'
        )
        self.assertEqual(400, response.status_code)
        self.assertEqual(str(response.data['fields']['error_message']), "You don't have the necessary permissions")

    def test_archive_entity(self):
        """Test archiving of Issuer and Badgeclasses and it's failures"""
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_delete=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher1)
        # cannot archive when unrevoked assertion present
        badgeclass_response = self.client.delete(
            '/issuer/badgeclasses/delete/{}'.format(badgeclass.entity_id), content_type='application/json'
        )
        self.assertEqual(badgeclass_response.status_code, 404)
        issuer_response = self.client.delete(
            '/issuer/delete/{}'.format(issuer.entity_id), content_type='application/json'
        )
        self.assertEqual(issuer_response.status_code, 404)
        assertion.revoke('For test reasons', student)
        # after revoking it should work
        issuer_response = self.client.delete(
            '/issuer/delete/{}'.format(issuer.entity_id), content_type='application/json'
        )
        self.assertEqual(issuer_response.status_code, 204)
        # and its child badgeclass is not gettable, as it has been archived
        query = 'query foo{badgeClass(id: "' + badgeclass.entity_id + '") { entityId name } }'
        response = self.graphene_post(teacher1, query)
        self.assertEqual(response['data']['badgeClass'], None)
        self.assertTrue(self.reload_from_db(issuer).archived)
        self.assertTrue(self.reload_from_db(badgeclass).archived)

    def test_cannot_delete_when_there_are_assertions(self):
        teacher1 = self.setup_teacher(authenticate=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        assertion = self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher1)
        response = self.client.delete(
            '/issuer/badgeclasses/delete/{}'.format(badgeclass.entity_id), content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        response = self.client.delete('/issuer/delete/{}'.format(issuer.entity_id), content_type='application/json')
        self.assertEqual(response.status_code, 404)

    def test_delete(self):
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_staff_membership(teacher1, teacher1.institution, may_delete=True)
        badgeclass_response = self.client.delete(
            '/issuer/badgeclasses/delete/{}'.format(badgeclass.entity_id), content_type='application/json'
        )
        self.assertEqual(badgeclass_response.status_code, 204)
        issuer_response = self.client.delete(
            '/issuer/delete/{}'.format(issuer.entity_id), content_type='application/json'
        )
        self.assertEqual(issuer_response.status_code, 204)
        self.assertTrue(self.instance_is_removed(badgeclass))
        self.assertTrue(self.instance_is_removed(issuer))
        self.assertEqual(faculty.cached_issuers().__len__(), 0)

    def test_enroll_and_award_badge(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(authenticate=True, affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        direct_award = self.setup_direct_award(
            badgeclass=badgeclass, eppn=student.eppns[0]
        )  # setup direct award, to check if it will be removed after awarding
        self.setup_staff_membership(teacher1, teacher1.institution, may_award=True, may_read=True)
        enroll_body = {'badgeclass_slug': badgeclass.entity_id}
        terms = badgeclass._get_terms()
        accept_terms_body = [{'terms_entity_id': terms.entity_id, 'accepted': True}]
        terms_accept_response = self.client.post(
            '/user/terms/accept', json.dumps(accept_terms_body), content_type='application/json'
        )
        enrollment_response = self.client.post(
            '/lti_edu/enroll', json.dumps(enroll_body), content_type='application/json'
        )
        self.assertEqual(enrollment_response.status_code, 201)
        self.client.logout()
        self.authenticate(teacher1)
        award_body = {
            'issue_signed': False,
            'create_notification': True,
            'enrollments': [
                {
                    'enrollment_entity_id': enrollment_response.data['entity_id'],
                    'evidence_items': [
                        {
                            'evidence_url': 'invalid.com',
                            'narrative': 'Some evidence narrative',
                            'name': 'Some name',
                            'description': 'Some description',
                        }
                    ],
                    'narrative': 'Some assertion narrative',
                }
            ],
        }
        failure_response = self.client.post(
            '/issuer/badgeclasses/award-enrollments/{}'.format(badgeclass.entity_id),
            json.dumps(award_body),
            content_type='application/json',
        )
        self.assertEqual(failure_response.status_code, 400)
        self.assertEqual(str(failure_response.data[0]['evidence_items'][0]['evidence_url'][0]), 'Enter a valid URL.')
        award_body['enrollments'][0]['evidence_items'][0]['evidence_url'] = 'https://www.valid.com'
        award_response = self.client.post(
            '/issuer/badgeclasses/award-enrollments/{}'.format(badgeclass.entity_id),
            json.dumps(award_body),
            content_type='application/json',
        )
        assertion = student.cached_badgeinstances().first()
        evidence = assertion.cached_evidence().first()  # test cache update
        self.assertEqual(evidence.evidence_url, 'https://www.valid.com')
        self.assertEqual(evidence.narrative, 'Some evidence narrative')
        self.assertEqual(evidence.name, 'Some name')
        self.assertEqual(evidence.description, 'Some description')
        self.assertEqual(assertion.narrative, 'Some assertion narrative')
        self.assertEqual(len(badgeclass.cached_assertions()), 1)  # test cache update
        self.assertEqual(award_response.status_code, 201)
        self.assertFalse(DirectAward.objects.filter(pk=direct_award.pk).exists())

    def test_enrollment_denial(self):
        teacher1 = self.setup_teacher(authenticate=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_staff_membership(
            teacher1, teacher1.institution, may_award=True, may_read=True, may_create=True, may_update=True
        )
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
        issuer = self.setup_issuer(teacher1, faculty=faculty)
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
    def test_issuer_uniqueness_constraint(self):
        """Checks if uniquness constraints on name trigger for Issuers"""
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        setup_issuer_kwargs = {'created_by': teacher1, 'faculty': faculty, 'name_english': 'EN', 'name_dutch': 'NL'}
        issuer = self.setup_issuer(**setup_issuer_kwargs)
        self.assertRaises(BadgrValidationMultipleFieldError, self.setup_issuer, **setup_issuer_kwargs)
        del setup_issuer_kwargs['name_english']
        self.assertRaises(BadgrValidationFieldError, self.setup_issuer, **setup_issuer_kwargs)

    def test_issuer_uniqueness_constraints_when_archiving(self):
        """Checks if uniquness constraints on name dont trigger for archived Issuers"""
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        setup_issuer_kwargs = {'created_by': teacher1, 'faculty': faculty, 'name_english': 'The same'}
        issuer = self.setup_issuer(**setup_issuer_kwargs)
        self.assertRaises(BadgrValidationFieldError, self.setup_issuer, **setup_issuer_kwargs)
        setup_issuer_kwargs['archived'] = True
        self.setup_issuer(**setup_issuer_kwargs)
        issuer.archive()

    def test_badgeclass_uniqueness_constraints_when_archiving(self):
        """Checks if uniquness constraints on name dont trigger for archived Badgeclasses"""
        teacher1 = self.setup_teacher(authenticate=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        setup_badgeclass_kwargs = {'created_by': teacher1, 'issuer': issuer, 'name': 'The same'}
        badgeclass = self.setup_badgeclass(**setup_badgeclass_kwargs)
        self.assertRaises(IntegrityError, self.setup_badgeclass, **setup_badgeclass_kwargs)
        setup_badgeclass_kwargs['archived'] = True
        self.setup_badgeclass(**setup_badgeclass_kwargs)
        badgeclass.archive()

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

    def test_recursive_archiving(self):
        """test archiving from Faculty down to Badgeclass and the uniqueness constraints on name that go with it"""
        teacher1 = self.setup_teacher(authenticate=True)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.setup_assertion(student, badgeclass, teacher1, revoked=True)
        staff = self.setup_staff_membership(teacher1, badgeclass)
        self.assertEqual(teacher1.cached_badgeclass_staffs(), [staff])
        self.assertRaises(ProtectedError, teacher1.institution.delete)
        self.assertRaises(ProtectedError, faculty.delete)
        self.assertRaises(ProtectedError, issuer.delete)
        self.assertRaises(ProtectedError, badgeclass.delete)
        faculty.archive()
        self.assertTrue(self.reload_from_db(faculty).archived)
        self.assertTrue(self.reload_from_db(issuer).archived)
        self.assertTrue(self.reload_from_db(badgeclass).archived)
        self.assertTrue(self.instance_is_removed(staff))
        self.assertEqual(teacher1.cached_badgeclass_staffs().__len__(), 0)
        self.assertEqual(faculty.cached_issuers().__len__(), 0)
        self.assertEqual(issuer.cached_badgeclasses().__len__(), 0)
        self.assertEqual(teacher1.institution.cached_faculties().__len__(), 0)

    def test_badgeinstance_get_json(self):
        teacher1 = self.setup_teacher()
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        evidence_items = [{'evidence_url': 'http://valid.com', 'narrative': 'Some narrative'}]
        assertion = self.setup_assertion(
            student, badgeclass, teacher1, evidence=evidence_items, narrative='assertion narrative'
        )
        assertion_data = assertion.get_json()
        self.assertEqual(assertion_data['evidence'][0]['id'], 'http://valid.com')
        self.assertEqual(assertion_data['narrative'], 'assertion narrative')


class IssuerSchemaTest(BadgrTestCase):
    def test_issuer_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_issuer(teacher1, faculty=faculty)
        query = 'query foo {issuers {entityId contentTypeId}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['issuers'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['issuers'][0]['entityId']))

    def test_badgeclass_schema(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer)
        self.setup_direct_award(badgeclass)
        query = 'query foo {badgeClasses {entityId contentTypeId directAwards {entityId badgeclass {entityId} } terms {entityId termsUrl {url excerpt language}}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['badgeClasses'][0]['contentTypeId']))
        self.assertTrue(bool(response['data']['badgeClasses'][0]['entityId']))
        self.assertTrue(bool(response['data']['badgeClasses'][0]['directAwards']))
        self.assertTrue(bool(response['data']['badgeClasses'][0]['terms']['termsUrl'][0]['language']))
        self.assertEqual(len(response['data']['badgeClasses'][0]['terms']['termsUrl']), 4)
