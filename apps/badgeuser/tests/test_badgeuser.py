import json
from django.contrib.contenttypes.models import ContentType
from mainsite.tests import BadgrTestCase


class BadgeuserTest(BadgrTestCase):

    def test_provision_existing_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_administrate_users=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        content_type = ContentType.objects.get_for_model(faculty)

        # failure
        teacher4 = self.setup_teacher()  # different institution
        invitation_json = {'content_type': content_type.pk,
                           'object_id': faculty.entity_id,
                           'email': teacher4.email,
                           'for_teacher': True,
                           'data': {'may_administrate_users': True}}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json), content_type='application/json')
        self.assertTrue(response.data['fields'].__str__() == 'May not invite user from other institution')

        # success for existing user
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        invitation_json['email'] = teacher2.email
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json), content_type='application/json')
        self.authenticate(teacher2)
        self.assertTrue(not not response.data['user'])
        teacher2.match_provisionments()  # happens at login
        self.assertTrue(not teacher2.get_permissions(faculty)['may_administrate_users'])
        response_provision_list = self.client.get('/v1/user/provisions', content_type='application/json')
        provisionment_entity_id = response_provision_list.data[0]['entity_id']
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
                           'data': {'may_administrate_users': True}}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json), content_type='application/json')
        self.assertTrue(not response.data['user'])

        # success for non existing user
        new_teacher = self.setup_teacher(institution=teacher1.institution, email=email)
        self.authenticate(new_teacher)
        new_teacher.match_provisionments()
        response_provision_list = self.client.get('/v1/user/provisions', content_type='application/json')
        provisionment_entity_id = response_provision_list.data[0]['entity_id']
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(faculty)['may_administrate_users'])

    def test_provision_issuer_badgeclass_entities(self):
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
                           'data': {'may_sign': True}}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json),
                                    content_type='application/json')
        invitation_json['object_id'] = badgeclass.entity_id
        invitation_json['content_type'] = ContentType.objects.get_for_model(badgeclass).pk
        invitation_json['data'] = {'may_update': True}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json),
                                    content_type='application/json')
        self.authenticate(new_teacher)
        response_provision_list = self.client.get('/v1/user/provisions', content_type='application/json')
        for provision in response_provision_list.data:
            self.client.post('/v1/user/provision/accept/{}'.format(provision['entity_id']),
                             data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(badgeclass)['may_sign']
                        and new_teacher.get_permissions(badgeclass)['may_update'])

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
                           'data': {'may_sign': True}}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json),
                                    content_type='application/json')
        self.assertTrue(not response.data['user'])
        new_teacher = self.setup_teacher(institution=teacher1.institution, email=email)
        self.authenticate(new_teacher)
        new_teacher.match_provisionments()
        response_provision_list = self.client.get('/v1/user/provisions', content_type='application/json')
        provisionment_entity_id = response_provision_list.data[0]['entity_id']
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
                           'data': {'may_sign': True}}
        response = self.client.post('/v1/user/provision/create', json.dumps(invitation_json),
                                    content_type='application/json')
        self.authenticate(new_teacher)
        response_provision_list = self.client.get('/v1/user/provisions', content_type='application/json')
        provisionment_entity_id = response_provision_list.data[0]['entity_id']
        self.client.post('/v1/user/provision/accept/{}'.format(provisionment_entity_id),
                         data=json.dumps({'accept': True}), content_type='application/json')
        self.assertTrue(new_teacher.get_permissions(institution)['may_sign'])