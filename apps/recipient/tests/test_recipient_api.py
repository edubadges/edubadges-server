import json
import os
import time

from allauth.account.models import EmailAddress
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from badgeuser.models import BadgeUser
from mainsite import TOP_DIR
from mainsite.tests import CachingTestCase

from pathway.models import Pathway, PathwayElement, PathwayElementBadge
from recipient.models import RecipientGroup, RecipientGroupMembership, RecipientProfile




class RecipientApiTests(APITestCase, CachingTestCase):
    fixtures = ['0001_initial_superuser', 'test_badge_objects.json']

    def setUp(self):
        super(RecipientApiTests, self).setUp()

    def create_group(self):
        # Authenticate as an editor of the issuer in question
        self.client.force_authenticate(user=get_user_model().objects.get(pk=3))
        data = {'name': 'Group of Testing', 'description': 'A group used for testing.'}
        return self.client.post('/v2/issuers/edited-test-issuer/recipient-groups', data)

    def create_pathway(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=3))
        data = {'name': 'Pathway of Testing', 'description': 'A pathway used for testing.'}
        return self.client.post('/v2/issuers/edited-test-issuer/pathways', data)

    def test_can_create_group(self):
        response = self.create_group()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Group of Testing')

    def test_can_delete_group(self):
        _ = self.create_group()

        response = self.client.delete('/v2/issuers/edited-test-issuer/recipient-groups/group-of-testing')
        self.assertEqual(response.status_code, 200)

        get_response = self.client.get('/v2/issuers/edited-test-issuer/recipient-groups/group-of-testing')
        self.assertEqual(get_response.status_code, 404)

    def test_can_add_member_to_group(self):
        self.create_group()

        member_data = {'name': 'Test Member', 'recipient': 'testmemberuno@example.com'}
        self.client.force_authenticate(user=get_user_model().objects.get(pk=3))
        response = self.client.post(
            '/v2/issuers/edited-test-issuer/recipient-groups/group-of-testing/members',
            member_data
        )

        self.assertEqual(response.status_code, 201)

        get_response = self.client.get('/v2/issuers/edited-test-issuer/recipient-groups/group-of-testing/members')
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
            '/v2/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
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
            '/v2/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
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
            '/v2/issuers/{}/recipient-groups/{}?embedRecipients=true'.format(group.issuer.slug, group.slug),
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
        response = self.client.put('/v2/issuers/edited-test-issuer/recipient-groups/group-of-testing', data)

        self.assertEqual(response.status_code, 200)
        instance = RecipientGroup.objects.first()
        self.assertEqual(instance.pathways.count(), 1)
        self.assertEqual(response.data['pathways'][0]['@id'], instance.pathways.first().jsonld_id)
        self.assertEqual(response.data['pathways'][0]['slug'], instance.pathways.first().slug)

    def test_list_group_pathway_subscriptions(self):
        pass