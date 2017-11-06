# encoding: utf-8
from __future__ import unicode_literals

import json

from mainsite.tests import BadgrTestCase, SetupIssuerHelper

from issuer.models import Issuer


class PublicAPITests(SetupIssuerHelper, BadgrTestCase):
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    def test_get_issuer_object(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)

        with self.assertNumQueries(0):
            response = self.client.get('/public/issuers/{}'.format(test_issuer.entity_id))
            self.assertEqual(response.status_code, 200)

    def test_get_issuer_object_that_doesnt_exist(self):
        fake_entity_id = 'imaginary-issuer'
        with self.assertRaises(Issuer.DoesNotExist):
            Issuer.objects.get(entity_id=fake_entity_id)

        # a db miss will generate 2 queries, lookup by entity_id and lookup by slug
        with self.assertNumQueries(2):
            response = self.client.get('/public/issuers/imaginary-issuer')
            self.assertEqual(response.status_code, 404)

    def test_get_badgeclass_image_with_redirect(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        with self.assertNumQueries(0):
            response = self.client.get('/public/badges/{}/image'.format(test_badgeclass.entity_id))
            self.assertEqual(response.status_code, 302)

    def test_get_assertion_image_with_redirect(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}/image'.format(assertion.entity_id), follow=False)
            self.assertEqual(response.status_code, 302)

    def test_get_assertion_json_explicit(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}'.format(assertion.entity_id),
                                       **{'HTTP_ACCEPT': 'application/json'})
            self.assertEqual(response.status_code, 200)

            # Will raise error if response is not JSON.
            content = json.loads(response.content)

            self.assertEqual(content['type'], 'Assertion')

    def test_get_assertion_json_implicit(self):
        """ Make sure we serve JSON by default if there is a missing Accept header. """
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}'.format(assertion.entity_id))
            self.assertEqual(response.status_code, 200)

            # Will raise error if response is not JSON.
            content = json.loads(response.content)

            self.assertEqual(content['type'], 'Assertion')

    def test_get_assertion_html(self):
        """ Ensure hosted Assertion page returns HTML if */* is requested and that it has OpenGraph metadata properties. """
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}'.format(assertion.entity_id),
                                       **{'HTTP_ACCEPT': '*/*'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')

    def test_get_assertion_html_linkedin(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}'.format(assertion.entity_id),
                                       **{'HTTP_USER_AGENT': 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')




