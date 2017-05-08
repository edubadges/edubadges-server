from django.contrib.auth.models import Permission

from badgeuser.models import BadgeUser, CachedEmailAddress
from issuer.models import Issuer
from mainsite.tests.base import BadgrTestCase
from recipient.models import RecipientGroup, RecipientProfile


class RecipientApiTests(BadgrTestCase):
    def setUp(self):
        self.test_user, _ = BadgeUser.objects.get_or_create(email='test@example.com')
        self.test_user.user_permissions.add(Permission.objects.get(codename="add_issuer"))
        CachedEmailAddress.objects.get_or_create(user=self.test_user, email='test@example.com', verified=True, primary=True)

        self.test_issuer, _ = Issuer.objects.get_or_create(
            name="Test Issuer",
            created_at="2015-04-08T15:18:16Z",
            created_by=self.test_user,
            slug="test-issuer"
        )

        super(RecipientApiTests, self).setUp()

    def create_group(self):
        # Authenticate as an editor of the issuer in question
        self.client.force_authenticate(user=self.test_user)
        data = {'name': 'Group of Testing', 'description': 'A group used for testing.'}
        return self.client.post('/v1/issuers/{}/recipient-groups'.format(self.test_issuer.slug), data)

    def create_pathway(self):
        self.client.force_authenticate(user=self.test_user)
        data = {'name': 'Pathway of Testing', 'description': 'A pathway used for testing.'}
        return self.client.post('/v1/issuers/{}/pathways'.format(self.test_issuer.slug), data)

    def test_can_create_group(self):
        response = self.create_group()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Group of Testing')

    def test_can_delete_group(self):
        _ = self.create_group()

        response = self.client.delete('/v1/issuers/{}/recipient-groups/group-of-testing'.format(self.test_issuer.slug))
        self.assertEqual(response.status_code, 200)

        get_response = self.client.get('/v1/issuers/{}/recipient-groups/group-of-testing'.format(self.test_issuer.slug))
        self.assertEqual(get_response.status_code, 404)

    def test_can_add_member_to_group(self):
        self.create_group()

        member_data = {'name': 'Test Member', 'recipient': 'testmemberuno@example.com'}
        self.client.force_authenticate(user=self.test_user)
        response = self.client.post(
            '/v1/issuers/{}/recipient-groups/group-of-testing/members'.format(self.test_issuer.slug),
            member_data
        )

        self.assertEqual(response.status_code, 201)

        get_response = self.client.get('/v1/issuers/{}/recipient-groups/group-of-testing/members'.format(self.test_issuer.slug))
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(len(get_response.data['memberships']), 1)

    def test_can_add_multiple_members_to_group(self):
        _ = self.create_group()

        group = RecipientGroup.objects.get(slug=_.data.get('slug'))

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sue", "email": "testersue@example.com"},
                {"name": "Tester Sammi", "email": "testersammi@example.com"}
            ]
        }"""

        response = self.client.put(
            '/v1/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
            data, content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 3)

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sue", "email": "testersue@example.com"}
            ]
        }"""

        response = self.client.put(
            '/v1/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
            data, content_type='application/json'
        )
        sammi = RecipientProfile.objects.get(recipient_identifier='testersammi@example.com')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 2)
        self.assertFalse(sammi in [m.recipient_profile for m in group.cached_members()])

        data = """{
            "members": [
                {"name": "Tester Steve", "email": "testersteve@example.com"},
                {"name": "Tester Sammi", "email": "testersammi@example.com"}
            ]
        }"""

        response = self.client.put(
            '/v1/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
            data, content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(group.cached_members()), 2)
        self.assertTrue(sammi in [m.recipient_profile for m in group.cached_members()])

    def test_can_delete_member_from_group(self):
        pass

    def test_subscribe_group_to_pathway(self):
        _ = self.create_group()
        pathway_response = self.create_pathway()

        data = {
            'pathways': [pathway_response.data.get('@id')]
        }
        response = self.client.put('/v1/issuers/{}/recipient-groups/group-of-testing'.format(self.test_issuer.slug), data)

        self.assertEqual(response.status_code, 200)
        instance = RecipientGroup.objects.first()
        self.assertEqual(instance.pathways.count(), 1)
        self.assertEqual(response.data['pathways'][0]['@id'], instance.pathways.first().jsonld_id)
        self.assertEqual(response.data['pathways'][0]['slug'], instance.pathways.first().slug)

    def test_list_group_pathway_subscriptions(self):
        group = self.create_group()

        pathway_response = self.create_pathway()

        data = {
            'pathways': [pathway_response.data.get('@id')]
        }
        response = self.client.put('/v1/issuers/{}/recipient-groups/group-of-testing'.format(self.test_issuer.slug), data)

        self.assertEqual(response.status_code, 200)
        instance = RecipientGroup.objects.first()
        self.assertEqual(instance.pathways.count(), 1)
        self.assertEqual(response.data['pathways'][0]['@id'], instance.pathways.first().jsonld_id)
        self.assertEqual(response.data['pathways'][0]['slug'], instance.pathways.first().slug)
