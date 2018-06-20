import base64

import json
import os

import collections

import datetime
import dateutil.parser
from django.urls import reverse
from django.utils import timezone
from openbadges.verifier.openbadges_context import (OPENBADGES_CONTEXT_V2_URI, OPENBADGES_CONTEXT_V1_URI,
                                                    OPENBADGES_CONTEXT_V2_DICT)
import responses
from openbadges_bakery import bake, unbake

from badgeuser.models import CachedEmailAddress, BadgeUser
from issuer.models import BadgeClass, Issuer, BadgeInstance
from mainsite.tests.base import BadgrTestCase, SetupIssuerHelper

from backpack.models import BackpackCollection, BackpackCollectionBadgeInstance
from backpack.serializers_v1 import (CollectionSerializerV1)
from mainsite.utils import first_node_match, OriginSetting
from issuer.utils import generate_sha256_hashstring, CURRENT_OBI_VERSION


dir = os.path.dirname(__file__)

def setup_basic_1_0(**kwargs):
    if not kwargs or not 'http://a.com/instance' in kwargs.get('exclude', []):
        responses.add(
            responses.GET, 'http://a.com/instance',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_instance.json')).read(),
            status=200, content_type='application/json'
        )
    if not kwargs or not 'http://a.com/badgeclass' in kwargs.get('exclude', []):
        responses.add(
            responses.GET, 'http://a.com/badgeclass',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_badgeclass.json')).read(),
            status=200, content_type='application/json'
        )
    if not kwargs or not 'http://a.com/issuer' in kwargs.get('exclude', []):
        responses.add(
            responses.GET, 'http://a.com/issuer',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_issuer.json')).read(),
            status=200, content_type='application/json'
        )
    if not kwargs or not 'http://a.com/badgeclass_image' in kwargs.get('exclude', []):
        responses.add(
            responses.GET, 'http://a.com/badgeclass_image',
            body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
            status=200, content_type='image/png'
        )


def setup_resources(resources):
    for item in resources:
        response_body = item.get('response_body')
        if response_body is None:
            response_body = open(os.path.join(dir, 'testfiles', item['filename'])).read()
        responses.add(
            responses.GET, item['url'],
            body=response_body,
            status=item.get('status', 200),
            content_type=item.get('content_type', 'application/json')

        )


def setup_basic_0_5_0(**kwargs):
    responses.add(
        responses.GET, 'http://oldstyle.com/instance',
        body=open(os.path.join(dir, 'testfiles/0_5_basic_instance.json')).read(),
        status=200, content_type='application/json'
    )
    if not kwargs or not 'http://oldstyle.com/images/1' in kwargs.get('exclude'):
        responses.add(
            responses.GET, 'http://oldstyle.com/images/1',
            body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
            status=200, content_type='image/png'
        )


class TestBadgeUploads(BadgrTestCase):

    @responses.activate
    def test_submit_basic_1_0_badge_via_url(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', token_scope='rw:backpack')

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )

        new_instance = BadgeInstance.objects.first()
        expected_url = "{}{}".format(OriginSetting.HTTP, reverse('badgeinstance_image', kwargs=dict(entity_id=new_instance.entity_id)))
        self.assertEqual(get_response.data[0].get('json', {}).get('image', {}).get('id'), expected_url)

    @responses.activate
    def test_submit_basic_1_1_badge_via_url(self):
        assertion_data = {
            '@context': 'https://w3id.org/openbadges/v1',
            'id': 'http://a.com/instance',
            'type': 'Assertion',
            "recipient": {"identity": "test@example.com", "hashed": False, "type": "email"},
            "badge": "http://a.com/badgeclass",
            "issuedOn": "2015-04-30",
            "verify": {"type": "hosted", "url": "http://a.com/instance"}
        }
        badgeclass_data = {
            '@context': 'https://w3id.org/openbadges/v1',
            'type': 'BadgeClass',
            'id': 'http://a.com/badgeclass',
            "name": "Basic Badge",
            "description": "Basic as it gets. v1.0",
            "image": "http://a.com/badgeclass_image",
            "criteria": "http://a.com/badgeclass_criteria",
            "issuer": "http://a.com/issuer"
        }
        issuer_data = {
            '@context': 'https://w3id.org/openbadges/v1',
            'type': 'Issuer',
            'id': 'http://a.com/issuer',
            "name": "Basic Issuer",
            "url": "http://a.com/issuer/website"
        }
        for d in [assertion_data, badgeclass_data, issuer_data]:
            responses.add(
                responses.GET, d['id'], json=d
            )

        responses.add(
            responses.GET, 'http://a.com/badgeclass_image',
            body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
            status=200, content_type='image/png'
        )

        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])

        self.setup_user(email='test@example.com', token_scope='rw:backpack')

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )

        new_instance = BadgeInstance.objects.first()
        expected_url = "{}{}".format(OriginSetting.HTTP, reverse('badgeinstance_image', kwargs=dict(entity_id=new_instance.entity_id)))
        self.assertEqual(get_response.data[0].get('json', {}).get('image', {}).get('id'), expected_url)

    @responses.activate
    def test_submit_basic_1_0_badge_via_url_plain_json(self):
        setup_basic_1_0()
        self.setup_user(email='test@example.com', token_scope='rw:backpack')
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges?json_format=plain', post_input
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data.get('json').get('badge').get('description'),
            u'Basic as it gets. v1.0'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_via_url_bad_email(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='not.test@email.example.com', authenticate=True)

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='VERIFY_RECIPIENT_IDENTIFIER',
        )))

    @responses.activate
    def test_submit_basic_1_0_badge_from_image_url_baked_w_assertion(self):
        setup_basic_1_0()
        self.setup_user(email='test@example.com', authenticate=True)
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])

        responses.add(
            responses.GET, 'http://a.com/baked_image',
            body=open(os.path.join(dir, 'testfiles/baked_image.png')).read(),
            status=200, content_type='image/png'
        )

        post_input = {
            'url': 'http://a.com/baked_image'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )


    @responses.activate
    def test_submit_basic_1_0_badge_image_png(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        image = open(os.path.join(dir, 'testfiles/baked_image.png'))
        post_input = {
            'image': image
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )

    @responses.activate
    def test_submit_baked_1_1_badge_preserves_metadata_roundtrip(self):
        assertion_metadata = {
            "@context": "https://w3id.org/openbadges/v1",
            "type": "Assertion",
            "id": "http://a.com/instance2",
            "recipient": {"identity": "test@example.com", "hashed": False, "type": "email"},
            "badge": "http://a.com/badgeclass",
            "issuedOn": "2015-04-30T00:00+00:00",
            "verify": {"type": "hosted", "url": "http://a.com/instance2"},
            "extensions:ExampleExtension": {
                "@context": "https://openbadgespec.org/extensions/exampleExtension/context.json",
                "type": ["Extension", "extensions:ExampleExtension"],
                "exampleProperty": "some extended text"
            },
            "schema:unknownMetadata": 55
        }
        badgeclass_metadata = {
            "@context": "https://w3id.org/openbadges/v1",
            "type": "BadgeClass",
            "id": "http://a.com/badgeclass",
            "name": "Basic Badge",
            "description": "Basic as it gets. v1.1",
            "image": "http://a.com/badgeclass_image",
            "criteria": "http://a.com/badgeclass_criteria",
            "issuer": "http://a.com/issuer"
        }
        issuer_metadata = {
            "@context": "https://w3id.org/openbadges/v1",
            "type": "Issuer",
            "id": "http://a.com/issuer",
            "name": "Basic Issuer",
            "url": "http://a.com/issuer/website"
        }

        with open(os.path.join(dir, 'testfiles/baked_image.png')) as image_file:
            original_image = bake(image_file, json.dumps(assertion_metadata))
            original_image.seek(0)

        responses.add(
            responses.GET, 'http://a.com/badgeclass_image',
            body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
            status=200, content_type='image/png'
        )

        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)},
            {'url': "https://openbadgespec.org/extensions/exampleExtension/context.json", 'response_body': json.dumps(
                {
                    "@context": {
                        "obi": "https://w3id.org/openbadges#",
                        "extensions": "https://w3id.org/openbadges/extensions#",
                        "exampleProperty": "http://schema.org/text"
                    },
                    "obi:validation": [
                        {
                            "obi:validatesType": "extensions:ExampleExtension",
                            "obi:validationSchema": "https://openbadgespec.org/extensions/exampleExtension/schema.json"
                        }
                    ]
                }
            )},
            {'url': "https://openbadgespec.org/extensions/exampleExtension/schema.json", 'response_body': json.dumps(
                {
                    "$schema": "http://json-schema.org/draft-04/schema#",
                    "title": "1.1 Open Badge Example Extension",
                    "description": "An extension that allows you to add a single string exampleProperty to an extension object to represent some of your favorite text.",
                    "type": "object",
                    "properties": {
                        "exampleProperty": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "exampleProperty"
                    ]
                }
            )},
            {'url': 'http://a.com/instance2', 'response_body': json.dumps(assertion_metadata)},
            {'url': 'http://a.com/badgeclass', 'response_body': json.dumps(badgeclass_metadata)},
            {'url': 'http://a.com/issuer', 'response_body': json.dumps(issuer_metadata)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        self.assertDictEqual(json.loads(unbake(original_image)), assertion_metadata)

        original_image.seek(0)
        response = self.client.post('/v1/earner/badges', {'image': original_image})
        self.assertEqual(response.status_code, 201)

        public_url = response.data.get('shareUrl')
        self.assertIsNotNone(public_url)
        response = self.client.get(public_url, Accept="application/json")

        for key in ['issuedOn']:
            fetched_ts = dateutil.parser.parse(response.data.get(key))
            metadata_ts = dateutil.parser.parse(assertion_metadata.get(key))
            self.assertEqual(fetched_ts, metadata_ts)

        for key in ['recipient', 'extensions:ExampleExtension']:
            fetched_dict = response.data.get(key)
            self.assertIsNotNone(fetched_dict, "Field '{}' is missing".format(key))
            metadata_dict = assertion_metadata.get(key)
            self.assertDictContainsSubset(metadata_dict, fetched_dict)

        for key in ['schema:unknownMetadata']:
            self.assertEqual(response.data.get(key), assertion_metadata.get(key))

    @responses.activate
    def test_submit_basic_1_0_badge_image_datauri_png(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        image = open(os.path.join(dir, 'testfiles/baked_image.png'))
        encoded = 'data:image/png;base64,' + base64.b64encode(image.read())
        post_input = {
            'image': encoded
        }
        response = self.client.post(
            '/v1/earner/badges', post_input, format='json'
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )
        # I think this test failure will be fixed by a badgecheck update to openbadges 1.0.1 as well

    @responses.activate
    def test_submit_basic_1_0_badge_assertion(self):
        setup_basic_1_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        post_input = {
            'assertion': open(os.path.join(dir, 'testfiles/1_0_basic_instance.json')).read()
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'), 'http://a.com/instance',
            "The badge in our backpack should report its JSON-LD id as its original OpenBadgeId"
        )

    @responses.activate
    def test_submit_basic_1_0_badge_url_variant_email(self):
        setup_basic_1_0(**{'exclude': 'http://a.com/instance'})
        setup_resources([
            {'url': 'http://a.com/instance3', 'filename': '1_0_basic_instance3.json'},
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        # add variant explicitly
        response = self.client.post('/v1/user/emails', dict(
            email='TEST@example.com'
        ))
        self.assertEqual(response.status_code, 400)  # adding a variant successfully returns a 400

        post_input = {
            'url': 'http://a.com/instance3',
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)

        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance3'
        )
        self.assertEqual(
            get_response.data[0].get('json', {}).get('recipient', {}).get('@value', {}).get('recipient'), 'TEST@example.com'
        )

        email = CachedEmailAddress.objects.get(email='test@example.com')
        self.assertTrue('TEST@example.com' in [e.email for e in email.cached_variants()])

    @responses.activate
    def test_submit_basic_1_0_badge_with_inaccessible_badge_image(self):
        setup_basic_1_0(**{'exclude': ['http://a.com/badgeclass_image']})
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
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='IMAGE_VALIDATION'
        )))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_issuer(self):
        setup_basic_1_0(**{'exclude': ['http://a.com/issuer']})
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
        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='FETCH_HTTP_NODE'
        )))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_badge_prop(self):
        self.setup_user(email='test@example.com', authenticate=True)

        responses.add(
            responses.GET, 'http://a.com/instance',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_instance_missing_badge_prop.json')).read(),
            status=200, content_type='application/json'
        )
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])

        post_input = {
            'url': 'http://a.com/instance'
        }

        response = self.client.post(
            '/v1/earner/badges', post_input
        )

        self.assertEqual(response.status_code, 400)
        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='VALIDATE_PROPERTY',
            prop_name='badge'
        )))

    @responses.activate
    def test_submit_basic_0_5_0_badge_via_url(self):
        setup_basic_0_5_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        post_input = {
            'url': 'http://oldstyle.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.data[0].get('json', {}).get('id'), post_input.get('url'),
                         "The badge in our backpack should report its JSON-LD id as the original OpenBadgeId")

    @responses.activate
    def test_submit_0_5_badge_upload_by_assertion(self):
        setup_basic_0_5_0()
        setup_resources([
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        post_input = {
            'assertion': open(os.path.join(dir, 'testfiles', '0_5_basic_instance.json')).read()
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        # TODO Update to support 0.5 badges

    @responses.activate
    def test_creating_no_duplicate_badgeclasses_and_issuers(self):
        setup_basic_1_0()
        setup_resources([
            {'url': 'http://a.com/instance2', 'filename': '1_0_basic_instance2.json'},
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        badgeclass_count = BadgeClass.objects.all().count()
        issuer_count = Issuer.objects.all().count()

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)

        post2_input = {
            'url': 'http://a.com/instance2'
        }
        response2 = self.client.post(
           '/v1/earner/badges', post2_input
        )
        self.assertEqual(response2.status_code, 201)

        self.assertEqual(BadgeClass.objects.all().count(), badgeclass_count+1)
        self.assertEqual(Issuer.objects.all().count(), issuer_count+1)

    def test_shouldnt_access_already_stored_badgeclass_for_validation(self):
        """
        TODO: If we already have a LocalBadgeClass saved for a URL,
        don't bother fetching again too soon.
        """
        pass

    def test_should_recheck_stale_localbadgeclass_in_validation(self):
        """
        TODO: If it has been more than a month since we last examined a LocalBadgeClass,
        maybe we should check
        it again.
        """
        pass
        # TODO: Re-evaluate badgecheck caching strategy

    @responses.activate
    def test_submit_badge_assertion_with_bad_date(self):
        setup_basic_1_0()
        setup_resources([
            {'url': 'http://a.com/instancebaddate', 'filename': '1_0_basic_instance_with_bad_date.json'},
            {'url': OPENBADGES_CONTEXT_V1_URI, 'filename': 'v1_context.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)}
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        post_input = {
            'url': 'http://a.com/instancebaddate'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='VALIDATE_PROPERTY',
            prop_name='issuedOn'
        )))

    @responses.activate
    def test_submit_badge_invalid_component_json(self):
        setup_basic_1_0(**{'exclude': ['http://a.com/issuer']})
        setup_resources([
            {'url': 'http://a.com/issuer', 'filename': '1_0_basic_issuer_invalid_json.json'},
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
        self.assertEqual(response.status_code, 400)

        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='FETCH_HTTP_NODE'
        )))

    @responses.activate
    def test_submit_badge_invalid_assertion_json(self):
        setup_resources([
            {'url': 'http://a.com/instance', 'filename': '1_0_basic_issuer_invalid_json.json'},
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
        self.assertEqual(response.status_code, 400)

        # openbadges returns FETCH_HTTP_NODE error when retrieving invalid json
        self.assertIsNotNone(first_node_match(response.data, dict(
            messageLevel='ERROR',
            name='FETCH_HTTP_NODE'
        )))

    @responses.activate
    def test_submit_badges_with_intragraph_references(self):
        setup_resources([
            {'url': 'http://a.com/assertion-embedded1', 'filename': '2_0_assertion_embedded_badgeclass.json'},
            {'url': OPENBADGES_CONTEXT_V2_URI, 'response_body': json.dumps(OPENBADGES_CONTEXT_V2_DICT)},
            {'url': 'http://a.com/badgeclass_image', 'filename': "unbaked_image.png"},
        ])
        self.setup_user(email='test@example.com', authenticate=True)

        assertion = {
            "@context": 'https://w3id.org/openbadges/v2',
            "id": 'http://a.com/assertion-embedded1',
            "type": "Assertion",
        }
        post_input = {
            'assertion': json.dumps(assertion)
        }
        response = self.client.post('/v1/earner/badges', post_input, format='json')
        self.assertEqual(response.status_code, 201)

class TestExpandAssertions(BadgrTestCase, SetupIssuerHelper):
    def test_no_expands(self):
        '''Expect correct result if no expand parameters are passed in'''

        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        test_recipient = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_badgeclass.issue(recipient_id='test_recipient@email.test')

        response = self.client.get('/v2/backpack/assertions')

        self.assertEqual(response.status_code, 200)
        # checking if 'badgeclass' was expanded into a dictionary
        self.assertTrue(not isinstance(response.data['result'][0]['badgeclass'], collections.OrderedDict))

    def test_expand_badgeclass_single_assertion_single_issuer(self):
        '''For a client with a single badge, attempting to expand the badgeclass without
        also expanding the issuer.'''

        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        test_recipient = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_badgeclass.issue(recipient_id='test_recipient@email.test')

        response = self.client.get('/v2/backpack/assertions?expand=badgeclass')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data['result'][0]['badgeclass'], collections.OrderedDict))
        self.assertTrue(not isinstance(response.data['result'][0]['badgeclass']['issuer'], collections.OrderedDict))

    def test_expand_issuer_single_assertion_single_issuer(self):
        '''For a client with a single badge, attempting to expand the issuer without
        also expanding the badgeclass should result in no expansion to the response.'''

        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        test_recipient = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_badgeclass.issue(recipient_id='test_recipient@email.test')

        responseOne = self.client.get('/v2/backpack/assertions?expand=issuer')
        responseTwo = self.client.get('/v2/backpack/assertions')

        self.assertEqual(responseOne.status_code, 200)
        self.assertEqual(responseTwo.status_code, 200)
        self.assertEqual(responseOne.data, responseTwo.data)

    def test_expand_badgeclass_and_isser_single_assertion_single_issuer(self):
        '''For a client with a single badge, attempting to expand the badgeclass and issuer.'''

        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        test_recipient = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_badgeclass.issue(recipient_id='test_recipient@email.test')

        response = self.client.get('/v2/backpack/assertions?expand=badgeclass&expand=issuer')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(response.data['result'][0]['badgeclass'], collections.OrderedDict))
        self.assertTrue(isinstance(response.data['result'][0]['badgeclass']['issuer'], collections.OrderedDict))

    def test_expand_badgeclass_mult_assertions_mult_issuers(self):
        '''For a client with multiple badges, attempting to expand the badgeclass without
        also expanding the issuer.'''

        # define users and issuers
        test_user = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_issuer_one = self.setup_issuer(name="Test Issuer 1",owner=test_user)
        test_issuer_two = self.setup_issuer(name="Test Issuer 2",owner=test_user)
        test_issuer_three = self.setup_issuer(name="Test Issuer 3",owner=test_user)

        # define badgeclasses
        test_badgeclass_one = self.setup_badgeclass(name='Test Badgeclass 1',issuer=test_issuer_one)
        test_badgeclass_two = self.setup_badgeclass(name='Test Badgeclass 2',issuer=test_issuer_one)
        test_badgeclass_three = self.setup_badgeclass(name='Test Badgeclass 3',issuer=test_issuer_two)
        test_badgeclass_four = self.setup_badgeclass(name='Test Badgeclass 4',issuer=test_issuer_three)
        test_badgeclass_five = self.setup_badgeclass(name='Test Badgeclass 5',issuer=test_issuer_three)
        test_badgeclass_six = self.setup_badgeclass(name='Test Badgeclass 6',issuer=test_issuer_three)

        # issue badges to user
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')

        response = self.client.get('/v2/backpack/assertions?expand=badgeclass')

        self.assertEqual(len(response.data['result']), 6)
        for i in range(6):
            self.assertTrue(isinstance(response.data['result'][i]['badgeclass'], collections.OrderedDict))
            self.assertTrue(not isinstance(response.data['result'][i]['badgeclass']['issuer'], collections.OrderedDict))

    def test_expand_badgeclass_and_issuer_mult_assertions_mult_issuers(self):
        '''For a client with multiple badges, attempting to expand the badgeclass and issuer.'''

        # define users and issuers
        test_user = self.setup_user(email='test_recipient@email.test', authenticate=True)
        test_issuer_one = self.setup_issuer(name="Test Issuer 1",owner=test_user)
        test_issuer_two = self.setup_issuer(name="Test Issuer 2",owner=test_user)
        test_issuer_three = self.setup_issuer(name="Test Issuer 3",owner=test_user)

        # define badgeclasses
        test_badgeclass_one = self.setup_badgeclass(name='Test Badgeclass 1',issuer=test_issuer_one)
        test_badgeclass_two = self.setup_badgeclass(name='Test Badgeclass 2',issuer=test_issuer_one)
        test_badgeclass_three = self.setup_badgeclass(name='Test Badgeclass 3',issuer=test_issuer_two)
        test_badgeclass_four = self.setup_badgeclass(name='Test Badgeclass 4',issuer=test_issuer_three)
        test_badgeclass_five = self.setup_badgeclass(name='Test Badgeclass 5',issuer=test_issuer_three)
        test_badgeclass_six = self.setup_badgeclass(name='Test Badgeclass 6',issuer=test_issuer_three)

        # issue badges to user
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')
        test_badgeclass_one.issue(recipient_id='test_recipient@email.test')

        response = self.client.get('/v2/backpack/assertions?expand=badgeclass&expand=issuer')

        self.assertEqual(len(response.data['result']), 6)
        for i in range(6):
            self.assertTrue(isinstance(response.data['result'][i]['badgeclass'], collections.OrderedDict))
            self.assertTrue(isinstance(response.data['result'][i]['badgeclass']['issuer'], collections.OrderedDict))




class TestCollections(BadgrTestCase):
    def setUp(self):
        super(TestCollections, self).setUp()
        self.user, _ = BadgeUser.objects.get_or_create(email='test@example.com')

        self.cached_email, _ = CachedEmailAddress.objects.get_or_create(user=self.user, email='test@example.com', verified=True, primary=True)

        self.issuer = Issuer.objects.create(
            name="Open Badges",
            created_at="2015-12-15T15:55:51Z",
            created_by=None,
            slug="open-badges",
            source_url="http://badger.openbadges.org/program/meta/bda68a0b505bc0c7cf21bc7900280ee74845f693",
            source="test-fixture",
            image=""
        )

        self.badge_class = BadgeClass.objects.create(
            name="MozFest Reveler",
            created_at="2015-12-15T15:55:51Z",
            created_by=None,
            slug="mozfest-reveler",
            criteria_text=None,
            source_url="http://badger.openbadges.org/badge/meta/mozfest-reveler",
            source="test-fixture",
            image="",
            issuer=self.issuer
        )

        self.local_badge_instance_1 = BadgeInstance.objects.create(
            recipient_identifier="test@example.com",
            badgeclass=self.badge_class,
            issuer=self.issuer,
            image="uploads/badges/local_badgeinstance_174e70bf-b7a8-4b71-8125-c34d1a994a7c.png",
            acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED
        )

        self.local_badge_instance_2 = BadgeInstance.objects.create(
            recipient_identifier="test@example.com",
            badgeclass=self.badge_class,
            issuer=self.issuer,
            image="uploads/badges/local_badgeinstance_174e70bf-b7a8-4b71-8125-c34d1a994a7c.png",
            acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED
        )

        self.local_badge_instance_3 = BadgeInstance.objects.create(
            recipient_identifier="test@example.com",
            badgeclass=self.badge_class,
            issuer=self.issuer,
            image="uploads/badges/local_badgeinstance_174e70bf-b7a8-4b71-8125-c34d1a994a7c.png",
            acceptance=BadgeInstance.ACCEPTANCE_ACCEPTED
        )

        self.collection = BackpackCollection.objects.create(
            created_by=self.user,
            description='The Freshest Ones',
            name='Fresh Badges',
            slug='fresh-badges'
        )

        BackpackCollection.objects.create(
            created_by=self.user,
            description='It\'s even fresher.',
            name='Cool New Collection',
            slug='cool-new-collection'
        )
        BackpackCollection.objects.create(
            created_by=self.user,
            description='Newest!',
            name='New collection',
            slug='new-collection'
        )

    def test_can_get_collection_list(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get('/v1/earner/collections')
        self.assertEqual(len(response.data), 3)
        self.assertEqual(response.data[0]['badges'], [])

    def test_can_get_collection_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/v1/earner/collections/fresh-badges')

        self.assertEqual(response.data['badges'], [])

    def test_can_define_collection(self):
        """
        Authorized user can create a new collection via API.
        """
        data = {
            'name': 'Fruity Collection',
            'description': 'Apples and Oranges',
            'published': True,
            'badges': [
                {'id': self.local_badge_instance_1.entity_id},
                {'id': self.local_badge_instance_2.entity_id, 'description': 'A cool badge'}
            ]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/v1/earner/collections', data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('published'))

        self.assertEqual([i['id'] for i in response.data.get('badges')], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

    def test_can_define_collection_serializer(self):
        """
        A new collection may be created directly via serializer.
        """
        data = {
            'name': 'Fruity Collection',
            'description': 'Apples and Oranges',
            'badges': [{'id': self.local_badge_instance_1.entity_id}, {'id': self.local_badge_instance_2.entity_id, 'description': 'A cool badge'}]
        }

        serializer = CollectionSerializerV1(data=data, context={'user': self.user})
        serializer.is_valid(raise_exception=True)
        collection = serializer.save()

        self.assertIsNotNone(collection.pk)
        self.assertEqual(collection.name, data['name'])
        self.assertEqual(collection.cached_badgeinstances().count(), 2)

    def test_can_delete_collection(self):
        """
        Authorized user may delete one of their defined collections.
        """
        collection = BackpackCollection.objects.filter(created_by_id=self.user.id).first()

        self.client.force_authenticate(user=self.user)
        response = self.client.delete('/v1/earner/collections/{}'.format(collection.entity_id))

        self.assertEqual(response.status_code, 204)

    def test_can_publish_unpublish_collection_serializer(self):
        """
        The CollectionSerializer should be able to update/delete a collection's share hash
        via update method.
        """
        collection = BackpackCollection.objects.first()
        self.assertIn(collection.share_url, ('', None))

        serializer = CollectionSerializerV1(
            collection,
            data={'published': True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertNotEqual(collection.share_url, '')
        self.assertTrue(collection.published)

        serializer = CollectionSerializerV1(
            collection,
            data={'published': False}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertFalse(collection.published)
        self.assertIn(collection.share_url, ('', None))

    def test_can_publish_unpublish_collection_api_share_method(self):
        """
        The CollectionSerializer should be able to update/delete a collection's share hash
        via the CollectionGenerateShare GET/DELETE methods.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            '/v1/earner/collections/fresh-badges/share'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.startswith('http'))

        collection = BackpackCollection.objects.get(pk=self.collection.pk)

        self.assertTrue(collection.published)

        response = self.client.delete('/v1/earner/collections/fresh-badges/share')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)

        self.assertFalse(self.collection.published)

    def test_can_add_remove_collection_badges_via_serializer(self):
        """
        The CollectionSerializer should be able to update an existing collection's badge list
        """
        collection = BackpackCollection.objects.first()
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        serializer = CollectionSerializerV1(
            collection,
            data={'badges': [{'id': self.local_badge_instance_1.entity_id}, {'id': self.local_badge_instance_2.entity_id}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        serializer = CollectionSerializerV1(
            collection,
            data={'badges': [{'id': self.local_badge_instance_2.entity_id}, {'id': self.local_badge_instance_3.entity_id}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_2.entity_id, self.local_badge_instance_3.entity_id])

    def test_can_add_remove_collection_badges_via_collection_detail_api(self):
        """
        A PUT request to the CollectionDetail view should be able to update the list of badges
        in a collection.
        """
        collection = BackpackCollection.objects.first()
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        data = {
            'badges': [{'id': self.local_badge_instance_1.entity_id}, {'id': self.local_badge_instance_2.entity_id}],
            'name': collection.name,
            'description': collection.description
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}'.format(collection.entity_id), data=data,
            format='json')

        self.assertEqual(response.status_code, 200)
        collection = BackpackCollection.objects.get(entity_id=response.data.get('slug'))  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        data = {
            'badges': [{'id': self.local_badge_instance_2.entity_id}, {'id': self.local_badge_instance_3.entity_id}],
            'name': collection.name,
        }
        response = self.client.put(
            '/v1/earner/collections/{}'.format(collection.entity_id),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data.get('badges')], [self.local_badge_instance_2.entity_id, self.local_badge_instance_3.entity_id])
        collection = BackpackCollection.objects.get(entity_id=response.data.get('slug'))  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_2.entity_id, self.local_badge_instance_3.entity_id])

    def test_can_add_remove_badges_via_collection_badge_detail_api(self):
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        data = [{'id': self.local_badge_instance_1.entity_id}, {'id': self.local_badge_instance_2.entity_id}]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/v1/earner/collections/{}/badges'.format(self.collection.entity_id), data=data,
            format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        collection = BackpackCollection.objects.first()  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        response = self.client.get('/v1/earner/collections/{}/badges'.format(collection.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = self.client.delete(
            '/v1/earner/collections/{}/badges/{}'.format(collection.entity_id, data[0]['id']),
            data=data, format='json')

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
        collection = BackpackCollection.objects.first()  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 1)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_2.entity_id])

    def test_can_add_remove_issuer_badges_via_api(self):
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        data = [
            {'id': self.local_badge_instance_1.entity_id},
            {'id': self.local_badge_instance_2.entity_id}
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/v1/earner/collections/{}/badges'.format(self.collection.entity_id), data=data,
            format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        self.assertEqual(self.collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in self.collection.cached_badgeinstances()], [self.local_badge_instance_1.entity_id, self.local_badge_instance_2.entity_id])

        response = self.client.get(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.entity_id, self.local_badge_instance_2.entity_id)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.entity_id, self.local_badge_instance_2.entity_id)
        )
        self.assertEqual(response.status_code, 204)

    def test_api_handles_null_description_and_adds_badge(self):
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        data = {
            'badges': [{'id': self.local_badge_instance_1.entity_id, 'description': None}],
            'name': self.collection.name,
        }

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}'.format(self.collection.entity_id), data=data,
            format='json')
        self.assertEqual(response.status_code, 200)

        entry = self.collection.cached_collects().first()
        self.assertEqual(entry.badgeinstance_id, self.local_badge_instance_1.pk)

    def test_can_add_remove_collection_badges_collection_badgelist_api(self):
        """
        A PUT request to the Collection BadgeList endpoint should update the list of badges
        n a collection
        """
        self.assertEqual(len(self.collection.cached_badgeinstances()), 0)

        data = [{'id': self.local_badge_instance_1.entity_id}, {'id': self.local_badge_instance_2.entity_id}]

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(self.collection.entity_id), data=data,
            format='json')

        self.assertEqual(response.status_code, 200)
        collection = BackpackCollection.objects.first()  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.pk for i in collection.cached_badgeinstances()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        data = [{'id': self.local_badge_instance_2.entity_id}, {'id': self.local_badge_instance_3.entity_id}]
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(collection.entity_id),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_2.entity_id, self.local_badge_instance_3.entity_id])
        collection = BackpackCollection.objects.first()  # reload
        self.assertEqual(collection.cached_badgeinstances().count(), 2)
        self.assertEqual([i.entity_id for i in collection.cached_badgeinstances()], [self.local_badge_instance_2.entity_id, self.local_badge_instance_3.entity_id])

    def xit_test_can_update_badge_description_in_collection_via_detail_api(self):
        self.assertEqual(self.collection.cached_badgeinstances().count(), 0)

        serializer = CollectionSerializerV1(
            self.collection,
            data={'badges': [{'id': self.local_badge_instance_1.pk},
                             {'id': self.local_badge_instance_2.pk}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(self.collection.cached_badgeinstances().count(), 2)

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.entity_id, self.local_badge_instance_1.pk),
            data={'id': 1, 'description': 'A cool badge.'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': self.local_badge_instance_1.pk, 'description': 'A cool badge.'})

        obj = BackpackCollectionBadgeInstance.objects.get(collection=self.collection, instance_id=self.local_badge_instance_1.pk)
        self.assertEqual(obj.description, 'A cool badge.')

    def test_badge_share_json(self):
        """
        Legacy Badge Share pages should redirect to public pages
        """
        response = self.client.get('/share/badge/{}'.format(self.local_badge_instance_1.pk), **dict(
            HTTP_ACCEPT="application/json"
        ))

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.get('Location', None), self.local_badge_instance_1.public_url)

    def test_badge_share_html(self):
        """
        Legacy Badge Share pages should redirect to public pages
        """
        response = self.client.get('/share/badge/{}'.format(self.local_badge_instance_1.entity_id), **dict(
            HTTP_ACCEPT='text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        ))

        self.assertEqual(response.status_code, 301)
        self.assertEqual(response.get('Location', None), self.local_badge_instance_1.public_url)
