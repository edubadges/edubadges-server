from mainsite.tests import BadgrTestCase


class MainGrapheneTest(BadgrTestCase):

    def test_pagination(self):
        teacher1 = self.setup_teacher(authenticate=True)
        self.setup_staff_membership(teacher1, teacher1.institution, may_read=True)
        faculty = self.setup_faculty(institution=teacher1.institution)
        issuer = self.setup_issuer(faculty=faculty, created_by=teacher1)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        student = self.setup_student(affiliated_institutions=[teacher1.institution])
        for x in range(8):
            self.setup_assertion(recipient=student, badgeclass=badgeclass, created_by=teacher1)
        query = 'query foo{' \
                    'badgeClass(id: "' + badgeclass.entity_id + '") { '\
                        'entityId ' \
                        'name ' \
                        'assertionsPaginated(first: 2){' \
                            'pageInfo { '\
                                'startCursor '\
                                'endCursor '\
                                'hasNextPage '\
                                'hasPreviousPage}'\
                            'edges {'\
                                'node {'\
                                    'entityId }}}}}'
        response = self.graphene_post(teacher1, query)
        end_cursor = response['data']['badgeClass']['assertionsPaginated']['pageInfo']['endCursor']
        assertions_entity_ids_1 = [edge['node']['entityId'] for edge in response['data']['badgeClass']['assertionsPaginated']['edges']]
        self.assertEqual(assertions_entity_ids_1.__len__(), 2)
        query = 'query foo{' \
                    'badgeClass(id: "' + badgeclass.entity_id + '") { '\
                        'entityId ' \
                        'name ' \
                        'assertionsPaginated(first: 3, after:"'+end_cursor+'"){' \
                            'pageInfo { '\
                                'startCursor '\
                                'endCursor '\
                                'hasNextPage '\
                                'hasPreviousPage}'\
                            'edges {'\
                                'node {'\
                                    'entityId }}}}}'
        response = self.graphene_post(teacher1, query)
        assertions_entity_ids_2 = [edge['node']['entityId'] for edge in
                                   response['data']['badgeClass']['assertionsPaginated']['edges']]
        self.assertEqual(assertions_entity_ids_2.__len__(), 3)
        self.assertFalse(all(entity_id in assertions_entity_ids_1 for entity_id in assertions_entity_ids_2))
