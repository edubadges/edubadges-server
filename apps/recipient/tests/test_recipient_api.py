import unittest
from mainsite.tests.base import BadgrTestCase, SetupIssuerHelper
from recipient.models import RecipientGroup, RecipientProfile


class RecipientApiTests(SetupIssuerHelper, BadgrTestCase):
    def setUp(self):
        super(RecipientApiTests, self).setUp()

        self.test_user = self.setup_user(authenticate=True)
        self.test_issuer = self.setup_issuer(owner=self.test_user)

    def create_group(self):
        url = '/v2/issuers/{}/recipient-groups'.format(self.test_issuer.entity_id)
        return self.client.post(url, {
            'name': 'Group of Testing',
            'description': 'A group used for testing.'
        })

    def create_pathway(self):
        return self.client.post('/v2/issuers/{}/pathways'.format(self.test_issuer.entity_id), {
            'name': 'Pathway of Testing',
            'description': 'A pathway used for testing.'
        })

    @unittest.skip('For debug speedup')
    def test_can_create_group(self):
        response = self.create_group()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Group of Testing')

    @unittest.skip('For debug speedup')
    def test_can_delete_group(self):
        response = self.create_group()
        self.assertIn('slug', response.data)
        group_slug = response.data.get('slug')

        response = self.client.delete('/v2/issuers/{issuer}/recipient-groups/{group}'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug))
        self.assertEqual(response.status_code, 204)

        get_response = self.client.get('/v2/issuers/{issuer}/recipient-groups/{group}'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug))
        self.assertEqual(get_response.status_code, 404)

    @unittest.skip('For debug speedup')
    def test_can_add_member_to_group(self):
        response = self.create_group()
        self.assertIn('slug', response.data)
        group_slug = response.data.get('slug')

        member_data = {'name': 'Test Member', 'recipient': 'testmemberuno@example.com'}
        response = self.client.post('/v2/issuers/{issuer}/recipient-groups/{group}/members'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug
        ), member_data)

        self.assertEqual(response.status_code, 201)

        get_response = self.client.get('/v2/issuers/{issuer}/recipient-groups/{group}/members'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug))

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data['memberships']), 1)

    @unittest.skip('For debug speedup')
    def test_can_add_multiple_members_to_group(self):
        response = self.create_group()
        self.assertIn('slug', response.data)
        group_slug = response.data.get('slug')
        group = RecipientGroup.cached.get(entity_id=group_slug)

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sue", "email": "testersue@example.com"},
                {"name": "Tester Sammi", "email": "testersammi@example.com"}
            ]
        }"""
        response = self.client.put('/v2/issuers/{issuer}/recipient-groups/{group}?embedRecipients=true'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug
        ), data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 3)

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sue", "email": "testersue@example.com"}
            ]
        }"""
        response = self.client.put('/v2/issuers/{issuer}/recipient-groups/{group}?embedRecipients=true'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug
        ), data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 2)
        sammi = RecipientProfile.objects.get(recipient_identifier='testersammi@example.com')
        self.assertFalse(sammi in [m.recipient_profile for m in group.cached_members()])

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sammi", "email": "testersammi@example.com"}
            ]
        }"""
        response = self.client.put('/v2/issuers/{issuer}/recipient-groups/{group}?embedRecipients=true'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug
        ), data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 2)
        self.assertTrue(sammi in [m.recipient_profile for m in group.cached_members()])

    @unittest.skip('For debug speedup')
    def test_subscribe_group_to_pathway(self):
        group_response = self.create_group()
        group_slug = group_response.data.get('slug')
        pathway_response = self.create_pathway()

        data = {
            'pathways': [pathway_response.data.get('@id')]
        }

        response = self.client.put('/v2/issuers/{issuer}/recipient-groups/{group}'.format(
            issuer=self.test_issuer.entity_id,
            group=group_slug
        ), data)

        self.assertEqual(response.status_code, 200)
        instance = RecipientGroup.objects.first()
        self.assertEqual(instance.pathways.count(), 1)
        self.assertEqual(response.data['pathways'][0]['@id'], instance.pathways.first().jsonld_id)
        self.assertEqual(response.data['pathways'][0]['slug'], instance.pathways.first().slug)

