# encoding: utf-8


import io
import json
import unittest
import responses
from django.urls import reverse
from openbadges.verifier.openbadges_context import OPENBADGES_CONTEXT_V1_URI, OPENBADGES_CONTEXT_V2_URI, \
    OPENBADGES_CONTEXT_V2_DICT
from openbadges_bakery import unbake

from backpack.models import BackpackCollection, BackpackCollectionBadgeInstance
from backpack.tests import setup_resources, setup_basic_1_0
from issuer.models import Issuer, BadgeInstance
from issuer.utils import CURRENT_OBI_VERSION, OBI_VERSION_CONTEXT_IRIS, UNVERSIONED_BAKED_VERSION
from mainsite.models import BadgrApp
from mainsite.tests import BadgrTestCase, SetupIssuerHelper
from mainsite.utils import OriginSetting


class PublicAPITests(SetupIssuerHelper, BadgrTestCase):
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    #@unittest.skip('For debug speedup')
    def test_get_issuer_object(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)

        with self.assertNumQueries(0):
            response = self.client.get('/public/issuers/{}'.format(test_issuer.entity_id))
            self.assertEqual(response.status_code, 200)

    #@unittest.skip('For debug speedup')
    def test_get_issuer_object_that_doesnt_exist(self):
        fake_entity_id = 'imaginary-issuer'
        with self.assertRaises(Issuer.DoesNotExist):
            Issuer.objects.get(entity_id=fake_entity_id)

        # a db miss will generate 2 queries, lookup by entity_id and lookup by slug
        with self.assertNumQueries(2):
            response = self.client.get('/public/issuers/imaginary-issuer')
            self.assertEqual(response.status_code, 404)

    #@unittest.skip('For debug speedup')
    def test_get_badgeclass_image_with_redirect(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        with self.assertNumQueries(0):
            response = self.client.get('/public/badges/{}/image'.format(test_badgeclass.entity_id))
            self.assertEqual(response.status_code, 302)

    #@unittest.skip('For debug speedup')
    def test_get_assertion_image_with_redirect(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/{}/image'.format(assertion.entity_id), follow=False)
            self.assertEqual(response.status_code, 302)

    #@unittest.skip('For debug speedup')
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

    #@unittest.skip('For debug speedup')
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

    #@unittest.skip('For debug speedup')
    def test_scrapers_get_html_stub(self):
        test_user_email = 'test.user@email.test'

        test_user = self.setup_user(authenticate=False, email=test_user_email)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id=test_user_email)

        # create a shared collection
        test_collection = BackpackCollection.objects.create(created_by=test_user, name='Test Collection', description="testing")
        BackpackCollectionBadgeInstance.objects.create(collection=test_collection, badgeinstance=assertion, badgeuser=test_user)  # add assertion to collection
        test_collection.published = True
        test_collection.save()
        self.assertIsNotNone(test_collection.share_url)

        testcase_headers = [
            # bots/scrapers should get an html stub with opengraph tags
            {'HTTP_USER_AGENT': 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'},
            {'HTTP_USER_AGENT': 'Twitterbot/1.0'},
            {'HTTP_USER_AGENT': 'facebook'},
            {'HTTP_USER_AGENT': 'Facebot'},
            {'HTTP_USER_AGENT': 'Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)'},
        ]

        # check that public assertion pages get og stubs served to bots
        for headers in testcase_headers:
            with self.assertNumQueries(0):
                response = self.client.get('/public/assertions/{}'.format(assertion.entity_id), **headers)
                self.assertEqual(response.status_code, 200)

                # should have received an html stub with og meta tags
                self.assertTrue(response.get('content-type').startswith('text/html'))
                self.assertContains(response, '<meta property="og:url" content="{}">'.format(assertion.public_url), html=True)
                png_image_url = "{}{}?type=png".format(
                    OriginSetting.HTTP,
                    reverse('badgeclass_image', kwargs={'entity_id': assertion.cached_badgeclass.entity_id})
                )
                self.assertContains(response, '<meta property="og:image" content="{}'.format(png_image_url))

        # check that collections get og stubs served to bots
        for headers in testcase_headers:
            with self.assertNumQueries(0):
                response = self.client.get(test_collection.share_url, **headers)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.get('content-type').startswith('text/html'))
                self.assertContains(response, '<meta property="og:url" content="{}">'.format(test_collection.share_url), html=True)

    #@unittest.skip('For debug speedup')
    def test_get_assertion_html_redirects_to_frontend(self):
        badgr_app = BadgrApp(cors='frontend.ui',
                             public_pages_redirect='http://frontend.ui/public')
        badgr_app.save()

        redirect_accepts = [
            {'HTTP_ACCEPT': 'application/xml,application/xhtml+xml,text/html;q=0.9, text/plain;q=0.8,image/png,*/*;q=0.5'},  # safari/chrome
            {'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'},  # firefox
            {'HTTP_ACCEPT': 'text/html, application/xhtml+xml, image/jxr, */*'},  # edge
        ]
        json_accepts = [
            {'HTTP_ACCEPT': '*/*'},  # curl
            {},  # no accept header
        ]

        with self.settings(BADGR_APP_ID=badgr_app.id):
            test_user = self.setup_user(authenticate=False)
            test_issuer = self.setup_issuer(owner=test_user)
            test_issuer.cached_badgrapp  # publish badgrapp to cache
            test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
            assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

            for headers in redirect_accepts:
                with self.assertNumQueries(0):
                    response = self.client.get('/public/assertions/{}'.format(assertion.entity_id), **headers)
                    self.assertEqual(response.status_code, 302)
                    self.assertEqual(response.get('Location'), 'http://frontend.ui/public/assertions/{}'.format(assertion.entity_id))

            for headers in json_accepts:
                with self.assertNumQueries(0):
                    response = self.client.get('/public/assertions/{}'.format(assertion.entity_id), **headers)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.get('Content-Type'), "application/ld+json")

    #@unittest.skip('For debug speedup')
    @responses.activate
    def test_uploaded_badge_returns_coerced_json(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        uploaded_badge = response.data
        assertion_entityid = uploaded_badge.get('id')
        assertion_url = '/public/assertions/{}?v=2_0'.format(assertion_entityid)
        response = self.client.get(assertion_url)
        self.assertEqual(response.status_code, 200)
        coerced_assertion = response.data
        assertion = BadgeInstance.objects.get(entity_id=assertion_entityid)
        self.assertDictEqual(coerced_assertion, assertion.get_json(obi_version="2_0"))
        # We should not change the declared jsonld ID of the requested object
        self.assertEqual(coerced_assertion.get('id'), 'http://a.com/instance')

    #@unittest.skip('For debug speedup')
    def verify_baked_image_response(self, assertion, response, obi_version, **kwargs):
        self.assertEqual(response.status_code, 200)
        baked_image = io.BytesIO(b"".join(response.streaming_content))
        baked_json = unbake(baked_image)
        baked_metadata = json.loads(baked_json)
        assertion_metadata = assertion.get_json(obi_version=obi_version, **kwargs)
        self.assertDictEqual(baked_metadata, assertion_metadata)

    #@unittest.skip('For debug speedup')
    def test_get_versioned_baked_images(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        response = self.client.get('/public/assertions/{}/image'.format(assertion.entity_id), follow=True)
        self.verify_baked_image_response(assertion, response, obi_version=UNVERSIONED_BAKED_VERSION)

        for obi_version in list(OBI_VERSION_CONTEXT_IRIS.keys()):
            response = self.client.get('/public/assertions/{assertion}/baked?v={version}'.format(
                assertion=assertion.entity_id,
                version=obi_version
            ), follow=True)

            if obi_version == UNVERSIONED_BAKED_VERSION:
                # current_obi_versions aren't re-baked expanded
                self.verify_baked_image_response(assertion, response, obi_version=obi_version)
            else:
                self.verify_baked_image_response(
                    assertion,
                    response,
                    obi_version=obi_version,
                    expand_badgeclass=True,
                    expand_issuer=True,
                    include_extra=True
                )

    #@unittest.skip('For debug speedup')
    def test_cache_updated_on_issuer_update(self):
        original_badgeclass_name = 'Original Badgeclass Name'
        new_badgeclass_name = 'new badgeclass name'

        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer, name=original_badgeclass_name)
        assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        response = self.client.get('/public/assertions/{}?expand=badge'.format(assertion.entity_id), Accept='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('badge', {}).get('name', None), original_badgeclass_name)

        test_badgeclass.name = new_badgeclass_name
        test_badgeclass.save()

        response = self.client.get('/public/assertions/{}?expand=badge'.format(assertion.entity_id), Accept='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('badge', {}).get('name', None), new_badgeclass_name)
