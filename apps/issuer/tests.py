from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.test import APIRequestFactory, APIClient, APITestCase, force_authenticate
from django.contrib.auth import get_user_model

import json
import os

from api import *
from serializers import *
from models import *

factory = APIRequestFactory()

example_issuer_props = {
    'name': 'Awesome Issuer',
    'description': 'An issuer of awe-inspiring credentials',
    'url': 'http://example.com',
    'email': 'contact@example.org'
}


class IssuerTests(TestCase):
    fixtures = ['0001_initial_superuser']

    def test_create_issuer_unauthenticated(self):
        view = IssuerList.as_view()

        request = factory.post(
            '/api/issuer/issuers',
            json.dumps(example_issuer_props),
            content_type='application/json'
        )

        response = view(request)
        self.assertEqual(response.status_code, 403)

    def test_create_issuer_authenticated(self):
        view = IssuerList.as_view()

        request = factory.post(
            '/api/issuer/issuers',
            json.dumps(example_issuer_props),
            content_type='application/json'
        )

        force_authenticate(request, user=get_user_model().objects.get(pk=1))
        response = view(request)
        self.assertEqual(response.status_code, 201)

        # assert that name, description, url, etc are set properly in response badge object
        badge_object = response.data.get('badge_object')
        self.assertEqual(badge_object['url'], example_issuer_props['url'])
        self.assertEqual(badge_object['name'], example_issuer_props['name'])
        self.assertEqual(badge_object['description'], example_issuer_props['description'])
        self.assertEqual(badge_object['email'], example_issuer_props['email'])
        self.assertIsNotNone(badge_object.get('id'))
        self.assertIsNotNone(badge_object.get('@context'))

    def test_private_issuer_detail_get(self):
        # GET on single badge should work if user has privileges
        # Eventually, implement PUT for updates (if permitted)
        pass


class BadgeClassTests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

    def test_create_badgeclass_for_issuer_authenticated(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/api/issuer/issuers/test-issuer/badges/',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

    def test_create_criteriatext_badgeclass_for_issuer_authenticated(self):
        """
        Ensure that when criteria text is submitted instead of a URL, the criteria address
        embedded in the badge is to the view that will display that criteria text
        (rather than the text itself or something...)
        """
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/api/issuer/issuers/test-issuer/badges/',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)
            self.assertRegexpMatches(response.data.get(
                'badge_object', {}).get('criteria'),
                r'badge-of-awesome/criteria$'
            )

    def test_create_badgeclass_for_issuer_unauthenticated(self):
        response = self.client.post('/api/issuer/issuers/test-issuer/badges/', {})
        self.assertEqual(response.status_code, 403)

    def test_badgeclass_list_authenticated(self):
        """
        Ensure that a logged-in user can get a list of their BadgeClasses
        """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/api/issuer/issuers/test-issuer/badges/')

        self.assertIsInstance(response.data, list)  # Ensure we receive a list of badgeclasses
        self.assertEqual(len(response.data), 1)  # Ensure that we receive the 1 badgeclass in fixture as expected

    def test_unauthenticated_cant_get_badgeclass_list(self):
        """
        Ensure that logged-out user can't GET the private API endpoint for badgeclass list
        """
        response = self.client.get('/api/issuer/issuers/test-issuer/badges/')
        self.assertEqual(response.status_code, 403)


class AssertionTests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

    def test_authenticated_owner_issue_badge(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        assertion = {
            "email": "test@example.com"
        }
        response = self.client.post('/api/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/', assertion)

        self.assertEqual(response.status_code, 201)

    def test_authenticated_nonowner_user_cant_issue(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=2))
        assertion = {
            "email": "test2@example.com"
        }
        response = self.client.post('/api/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/', assertion)

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cant_issue(self):
        assertion = {"email": "test@example.com"}
        response = self.client.post('/api/issuer/issuers/test-issuer/badges/', assertion)
        self.assertEqual(response.status_code, 403)

    def test_authenticated_owner_list_assertions(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/api/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_revoke_assertion(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete(
            '/api/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/9ecff8b2-a178-4d17-b382-9109065012d1',
            {'revocation_reason': 'Earner kind of sucked, after all.'}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/public/assertions/9ecff8b2-a178-4d17-b382-9109065012d1')
        self.assertEqual(response.status_code, 410)

    def test_revoke_assertion_missing_reason(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete(
            '/api/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/9ecff8b2-a178-4d17-b382-9109065012d1',
            {}
        )

        self.assertEqual(response.status_code, 400)

class PublicAPITests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    def test_get_issuer_object(self):
        response = self.client.get('/public/issuers/test-issuer')
        self.assertEqual(response.status_code, 200)

    def test_get_issuer_object_that_doesnt_exist(self):
        response = self.client.get('/public/issuers/imaginary-issuer')
        self.assertEqual(response.status_code, 404)

    def test_get_badgeclass_image_with_redirect(self):
        response = self.client.get('/public/badges/badge-of-testing/image')
        self.assertEqual(response.status_code, 302)

    def test_get_assertion_image_with_redirect(self):
        response = self.client.get('/public/assertions/9ecff8b2-a178-4d17-b382-9109065012d1/image')
        self.assertEqual(response.status_code, 302)
