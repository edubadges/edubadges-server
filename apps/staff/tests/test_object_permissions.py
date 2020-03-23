import json
from mainsite.tests import BadgrTestCase
from mainsite.tests.base import SetupUserHelper, ObjectSetupHelper, SetupStaffHelper


class ObjectPermissionTests(BadgrTestCase, SetupUserHelper, ObjectSetupHelper, SetupStaffHelper):

    def test_may_not_administrate_user(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=False)
        data = json.dumps({
            "may_create": 0,
            "may_read": 1,
            "may_update": 0,
            "may_delete": 0,
            "may_sign": 0,
            "may_award": 0,
            "may_administrate_users": 0,
            "user": teacher2.entity_id,
            "faculty": faculty.entity_id
        })
        response = self.client.post('/staff/faculty/{}/create'.format(faculty.entity_id),
                                    data, content_type='application/json')
        self.assertEqual(404, response.status_code)

    def test_may_not_assign_perms_you_dont_have(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        data = json.dumps({
            "may_create": 1,
            "may_read": 1,
            "may_update": 1,
            "may_delete": 1,
            "may_sign": 1,
            "may_award": 1,
            "may_administrate_users": 0,
            "user": teacher2.entity_id,
            "faculty": faculty.entity_id
        })
        response = self.client.post('/staff/faculty/{}/create'.format(faculty.entity_id),
                                    data, content_type='application/json')
        self.assertEqual("May not assign permissions that you don't have yourself", str(response.data[0]))

    def test_create_issuer_staff(self):
        teacher1 = self.setup_teacher(authenticate=True)
        teacher2 = self.setup_teacher(institution=teacher1.institution)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True, may_administrate_users=True)
        data = json.dumps({
            "may_create": 0,
            "may_read": 1,
            "may_update": 0,
            "may_delete": 0,
            "may_sign": 0,
            "may_award": 0,
            "may_administrate_users": 1,
            "user": teacher2.entity_id,
            "issuer": issuer.entity_id
        })
        response = self.client.post('/staff/issuer/{}/create'.format(issuer.entity_id),
                                    data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
