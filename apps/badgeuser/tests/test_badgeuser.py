import json
from django.contrib.contenttypes.models import ContentType
from mainsite.tests import BadgrTestCase
from badgeuser.models import UserProvisionment
from mainsite.exceptions import BadgrValidationError


class BadgeuserProvisionmentTest(BadgrTestCase):

    def test_provision_existing_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        content_type = ContentType.objects.get_for_model(faculty)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        invitation_json = {'content_type': content_type.pk,
                           'object_id': faculty.entity_id,
                           'email': teacher2.email,
                           'for_teacher': True,
                           'data': {'may_administrate_users': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertTrue(not not response.data[0]['message']['user'])
        teacher2.match_provisionments()  # happens at login
        self.assertTrue(not teacher2.get_permissions(faculty)['may_administrate_users'])
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(teacher2, query)
        provisionment_entity_id = response_userprovisionments['data']['currentUser']['userprovisionments'][0]['entityId']
        self.authenticate(teacher2)
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(teacher2.get_permissions(faculty)['may_administrate_users'])

    def test_provision_non_existing_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        email = 'eenof@anderemail1.adres'
        content_type = ContentType.objects.get_for_model(faculty)
        invitation_json = {'content_type': content_type.pk,
                           'object_id': faculty.entity_id,
                           'email': email,
                           'for_teacher': True,
                           'data': {'may_administrate_users': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertTrue(not response.data[0]['message']['user'])

        # success for non existing user
        new_teacher = self.setup_teacher(institution=teacher1.institution, email=email)
        new_teacher.match_provisionments()
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(new_teacher, query)
        provisionment_entity_id = response_userprovisionments['data']['currentUser']['userprovisionments'][0]['entityId']
        self.authenticate(new_teacher)
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(faculty)['may_administrate_users'])

    def test_provision_issuer(self):
        # test for issuer & badgeclass
        teacher1 = self.setup_teacher(authenticate=True)
        new_teacher = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.authenticate(teacher1)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        invitation_json = {'content_type': ContentType.objects.get_for_model(issuer).pk,
                           'object_id': issuer.entity_id,
                           'email': new_teacher.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(new_teacher, query)
        userprovisionments = response_userprovisionments['data']['currentUser']['userprovisionments']
        self.authenticate(new_teacher)
        for provision in userprovisionments:
            self.client.post('/v1/user/provision/accept/{}'.format(provision['entityId']),
                             data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(badgeclass)['may_sign'])

    def test_provision_badgeclass(self):
        # test for issuer & badgeclass
        teacher1 = self.setup_teacher(authenticate=True)
        new_teacher = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.authenticate(teacher1)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        invitation_json = {'content_type': ContentType.objects.get_for_model(badgeclass).pk,
                           'object_id': badgeclass.entity_id,
                           'email': new_teacher.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(new_teacher, query)
        userprovisionments = response_userprovisionments['data']['currentUser']['userprovisionments']
        self.authenticate(new_teacher)
        for provision in userprovisionments:
            self.client.post('/v1/user/provision/accept/{}'.format(provision['entityId']),
                             data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(badgeclass)['may_sign'])

    def test_provision_non_exitisting_user_for_institution_staff(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        institution = teacher1.institution
        #non existing
        email = 'eenof@anderemail4.adres'
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        self.assertTrue(not response.data[0]['message']['user'])
        new_teacher = self.setup_teacher(institution=teacher1.institution, email=email)
        new_teacher.match_provisionments()
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(new_teacher, query)
        provisionment_entity_id = response_userprovisionments['data']['currentUser']['userprovisionments'][0]['entityId']
        self.authenticate(new_teacher)
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(institution)['may_sign'])

    def test_provision_existing_user_for_institution_staff(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        institution = teacher1.institution
        new_teacher = self.setup_teacher(institution=teacher1.institution)
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': new_teacher.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        query = 'query foo {currentUser {entityId userprovisionments {entityId}}}'
        response_userprovisionments = self.graphene_post(new_teacher, query)
        provisionment_entity_id = response_userprovisionments['data']['currentUser']['userprovisionments'][0]['entityId']
        self.authenticate(new_teacher)
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(institution)['may_sign'])

    def test_edit_delete_provisionment(self):
        teacher1 = self.setup_teacher(authenticate=True)
        unauthorized_teacher = self.setup_teacher()
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        institution = teacher1.institution
        email = 'eenof@anderemail5.adres'
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION
                           }
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        new_teacher = self.setup_teacher(institution=teacher1.institution, email=email)
        new_teacher.match_provisionments()
        invitation_edit = {'data': {'may_sign': False}, 'email': 'kjajajaj'}
        # test unauthorized
        self.authenticate(unauthorized_teacher)
        invitation_entity_id = response.data[0]['message']['entity_id']
        failed_response = self.client.put('/v1/user/provision/edit/{}'.format(invitation_entity_id), json.dumps(invitation_edit), content_type='application/json')
        self.assertEqual(failed_response.status_code, 404)
        failed_response = self.client.delete('/v1/user/provision/edit/{}'.format(invitation_entity_id))
        self.assertEqual(failed_response.status_code, 404)
        self.authenticate(teacher1)
        response = self.client.put('/v1/user/provision/edit/{}'.format(invitation_entity_id), json.dumps(invitation_edit), content_type='application/json')
        self.assertEqual(response.data['data']['may_sign'], False)
        query = 'query foo {currentUser {entityId userprovisionments {data, entityId}}}'
        response = self.graphene_post(new_teacher, query)
        self.assertEqual(response['data']['currentUser']['userprovisionments'][0]['data']['may_sign'], False)  # check instant cache update
        userprovisionment_entity_id = response['data']['currentUser']['userprovisionments'][0]['entityId']
        response = self.client.delete('/v1/user/provision/edit/{}'.format(userprovisionment_entity_id))
        self.assertEqual(response.status_code, 204)
        response = self.graphene_post(new_teacher, query)
        self.assertEqual(response['data']['currentUser']['userprovisionments'], [])

    def test_multiple_overlapping_staff_invites_for_one_user_failure(self):
        teacher1 = self.setup_teacher(authenticate=True)
        institution = teacher1.institution
        email = 'eenof@anderemail6.adres'
        self.setup_staff_membership(teacher1, institution, may_read=True, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_FIRST_ADMIN_INVITATION}
        self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')

        invitation_json['content_type'] = ContentType.objects.get_for_model(faculty).pk
        invitation_json['object_id'] = faculty.entity_id
        invitation_json['email'] = email
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertEqual(response.data[0]['message']['fields']['error_message'].__str__(), 'There may be only one invite per email address.')

    def test_provisionment_for_other_institution_failure(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        existing_non_colleague = self.setup_teacher()
        # test sending invite for own institution, but accepted by someone outside
        invitation_json = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                           'object_id': faculty.entity_id,
                           'email': existing_non_colleague.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response_failure = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertEqual(response_failure.data[0]['message']['fields']['error_message'].__str__(), 'May not invite user from other institution')
        new_non_colleague_email = 'new_non_colleague@mail.adres'
        invitation_json['email'] = new_non_colleague_email
        response_success = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        new_non_colleague = self.setup_teacher(email=new_non_colleague_email)
        failing_provisionment = UserProvisionment.objects.get(entity_id=response_success.data[0]['message']['entity_id'])
        try:
            failing_provisionment.match_user(new_non_colleague)
            self.assertTrue(False)
        except BadgrValidationError:
            self.assertTrue(True)
        # test sending invite for own institution, but accepted by someone outside
        teacher2 = self.setup_teacher()
        other_insitution = teacher2.institution
        invitation_json['content_type'] = ContentType.objects.get_for_model(other_insitution).pk
        invitation_json['object_id'] = other_insitution.entity_id
        invitation_json['email'] = 'some@randomemail.dontmatter'
        response_failure = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertEqual(response_failure.data[0]['message']['fields']['error_message'].__str__(), 'You do not have permission to invite user for this entity.')

    def test_provisionment_invite_staff_collision_throws_exception(self):
        teacher1 = self.setup_teacher(authenticate=True)
        colleague = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        self.setup_staff_membership(colleague, teacher1.institution, may_read=True, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        invitation_json = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                           'object_id': faculty.entity_id,
                           'email': colleague.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response_failure = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertEqual(response_failure.data[0]['message']['fields']['error_message'].__str__(), 'Cannot invite user for this entity. There is a conflicting staff membership.')

    def test_provisionment_invite_collides_with_other_invitation(self):
        teacher1 = self.setup_teacher(authenticate=True)
        colleague = self.setup_teacher(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        invitation_faculty = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                           'object_id': faculty.entity_id,
                           'email': colleague.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        invitation_issuer = {'content_type': ContentType.objects.get_for_model(issuer).pk,
                              'object_id': issuer.entity_id,
                              'email': colleague.email,
                              'for_teacher': True,
                              'data': {'may_sign': True},
                              'type': UserProvisionment.TYPE_INVITATION}
        response_failure = self.client.post('/v1/user/provision/create',
                                            json.dumps([invitation_faculty, invitation_issuer]),
                                            content_type='application/json')
        self.assertEqual(response_failure.data[1]['message']['fields']['error_message'].__str__(), 'Cannot invite user for this entity. There is a conflicting invite.')

    def test_provision_multiple_users(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        new_colleague_email = 'new_colleague@email.adress'
        colleage = self.setup_teacher(institution=teacher1.institution)
        invitation1 = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                       'object_id': faculty.entity_id,
                       'email': new_colleague_email,
                       'for_teacher': True,
                       'data': {'may_administrate_users': True},
                       'type': UserProvisionment.TYPE_INVITATION}
        invitation2 = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                       'object_id': faculty.entity_id,
                       'email': colleage.email,
                       'for_teacher': True,
                       'data': {'may_administrate_users': True},
                       'type': UserProvisionment.TYPE_INVITATION}
        failing_post_on_validation = {'content_type': ContentType.objects.get_for_model(faculty).pk,
                                      'object_id': faculty.entity_id,
                                      'email': 'invalid',
                                      'for_teacher': True,
                                      'data': {'may_administrate_users': True},
                                      'type': UserProvisionment.TYPE_INVITATION}
        failing_post_on_save = invitation1
        response = self.client.post('/v1/user/provision/create',
                                    json.dumps([invitation1, invitation2, failing_post_on_save,
                                                failing_post_on_validation]),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data.__len__(), 4)


class BadgeuserTermsTest(BadgrTestCase):

    def test_user_accept_general_terms(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.assertFalse(teacher1.general_terms_accepted())
        teacher1.accept_general_terms()
        self.assertTrue(teacher1.general_terms_accepted())
        student1 = self.setup_student()
        self.assertFalse(student1.general_terms_accepted())
        student1.accept_general_terms()
        self.assertTrue(student1.general_terms_accepted())
        self.increment_general_terms_version(student1)  # update terms
        self.increment_general_terms_version(teacher1)
        self.assertFalse(teacher1.general_terms_accepted())
        self.assertFalse(student1.general_terms_accepted())
        student1.accept_general_terms()
        teacher1.accept_general_terms()
        self.assertTrue(teacher1.general_terms_accepted())
        self.assertTrue(student1.general_terms_accepted())

    def test_student_accept_badge_terms(self):
        teacher1 = self.setup_teacher()
        student1 = self.setup_student(authenticate=True, affiliated_institutions=[teacher1.institution])
        issuer = self.setup_issuer(teacher1)
        badgeclass = self.setup_badgeclass(issuer)
        enroll_body = {"badgeclass_slug": badgeclass.entity_id}
        enrollment_response_failure = self.client.post("/lti_edu/enroll", json.dumps(enroll_body),
                                                       content_type='application/json')
        self.assertEqual(enrollment_response_failure.status_code, 400)
        self.assertFalse(badgeclass.terms_accepted(student1))
        terms = badgeclass._get_terms()
        accept_terms_body = [{'terms_entity_id': terms.entity_id, 'accepted': True}]
        terms_accept_response = self.client.post("/v1/user/terms/accept", json.dumps(accept_terms_body),
                                                 content_type='application/json')
        self.assertEqual(terms_accept_response.status_code, 201)
        enrollment_response_success = self.client.post("/lti_edu/enroll", json.dumps(enroll_body),
                                                       content_type='application/json')
        self.assertEqual(enrollment_response_success.status_code, 201)
        self.assertTrue(badgeclass.terms_accepted(student1))


class BadgeuserGraphqlTest(BadgrTestCase):

    def test_current_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        institution = teacher1.institution
        new_teacher = self.setup_teacher(institution=teacher1.institution)
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': new_teacher.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        response = self.client.post('/v1/user/provision/create', json.dumps([invitation_json]),
                                    content_type='application/json')
        query = 'query foo {currentUser {' \
                'entityId ' \
                'generalTerms {entityId} ' \
                'termsAgreements {agreed agreedVersion ' \
                    'terms {entityId, termsType, version, ' \
                    'institution {entityId}' \
                    'termsUrl {url, language}}}'\
                'userprovisionments {entityId ' \
                    'contentType {id}' \
                '}}}'
        response = self.graphene_post(new_teacher, query)
        self.assertTrue(bool(response['data']['currentUser']['userprovisionments'][0]['contentType']['id']))

    def test_userprovisionment_exposed_in_entities(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        new_teacher = self.setup_teacher(institution=teacher1.institution)
        institution = teacher1.institution
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(created_by=teacher1, faculty=faculty)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        self.assertEqual(institution.cached_userprovisionments().__len__(), 0)
        self.assertEqual(faculty.cached_userprovisionments().__len__(), 0)
        self.assertEqual(issuer.cached_userprovisionments().__len__(), 0)
        self.assertEqual(badgeclass.cached_userprovisionments().__len__(), 0)
        invitation_json = {'content_type': ContentType.objects.get_for_model(institution).pk,
                           'object_id': institution.entity_id,
                           'email': new_teacher.email,
                           'for_teacher': True,
                           'data': {'may_sign': True},
                           'type': UserProvisionment.TYPE_INVITATION}
        self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        new_teacher2 = self.setup_teacher(institution=teacher1.institution)
        invitation_json['content_type'] = ContentType.objects.get_for_model(faculty).pk
        invitation_json['object_id'] = faculty.entity_id
        invitation_json['email'] = new_teacher2.email
        self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        new_teacher3 = self.setup_teacher(institution=teacher1.institution)
        invitation_json['content_type'] = ContentType.objects.get_for_model(issuer).pk
        invitation_json['object_id'] = issuer.entity_id
        invitation_json['email'] = new_teacher3.email
        self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        new_teacher4 = self.setup_teacher(institution=teacher1.institution)
        invitation_json['content_type'] = ContentType.objects.get_for_model(badgeclass).pk
        invitation_json['object_id'] = badgeclass.entity_id
        invitation_json['email'] = new_teacher4.email
        self.client.post('/v1/user/provision/create', json.dumps([invitation_json]), content_type='application/json')
        self.assertEqual(institution.cached_userprovisionments().__len__(), 1)
        self.assertEqual(faculty.cached_userprovisionments().__len__(), 1)
        self.assertEqual(issuer.cached_userprovisionments().__len__(), 1)
        self.assertEqual(badgeclass.cached_userprovisionments().__len__(), 1)
        query = 'query foo {institutions {userprovisionments {entityId}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['institutions'][0]['userprovisionments'][0]['entityId']))
        query = 'query foo {faculties {userprovisionments {entityId}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['faculties'][0]['userprovisionments'][0]['entityId']))
        query = 'query foo {issuers {userprovisionments {entityId}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['issuers'][0]['userprovisionments'][0]['entityId']))
        query = 'query foo {badgeClasses {userprovisionments {entityId}}}'
        response = self.graphene_post(teacher1, query)
        self.assertTrue(bool(response['data']['badgeClasses'][0]['userprovisionments'][0]['entityId']))
