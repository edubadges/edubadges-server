# encoding: utf-8
from __future__ import unicode_literals

import json
import unittest
from unittest import skip

import datetime
import dateutil.parser
import png
import pytz
from django.apps import apps
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import timezone

from mainsite.tests import BadgrTestCase, SetupIssuerHelper
from openbadges_bakery import unbake

from issuer.models import BadgeInstance, IssuerStaff, BadgeClass
from mainsite.utils import OriginSetting

class AssertionTests(SetupIssuerHelper, BadgrTestCase):

    @skip("test does not pass when using FileStorage, but does when using S3BotoStorage, and behavior works as expected in server")
    def test_can_rebake_assertion(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        import issuer.utils

        # issue badge that gets baked with 1_1, while current version is 2_0
        issuer.utils.CURRENT_OBI_VERSION = '2_0'
        issuer.utils.UNVERSIONED_BAKED_VERSION = '1_1'
        test_assertion = test_badgeclass.issue(recipient_id='test1@email.test')
        v1_data = json.loads(str(unbake(test_assertion.image)))

        self.assertDictContainsSubset({
            '@context': u'https://w3id.org/openbadges/v1'
        }, v1_data)

        original_image_url = test_assertion.image_url()
        test_assertion.rebake()
        self.assertEqual(original_image_url, test_assertion.image_url())

        v2_datastr = unbake(test_assertion.image)
        self.assertTrue(v2_datastr)
        v2_data = json.loads(v2_datastr)
        self.assertDictContainsSubset({
            '@context': u'https://w3id.org/openbadges/v2'
        }, v2_data)

    #@unittest.skip('For debug speedup')
    def test_put_rebakes_assertion(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_assertion = test_badgeclass.issue(recipient_id='test1@email.test')

        # v1 api
        v1_backdate = datetime.datetime(year=2021, month=3, day=3, tzinfo=pytz.UTC)
        updated_data = dict(
            expires=v1_backdate.isoformat()
        )

        response = self.client.put('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_assertion.cached_issuer.entity_id,
            badge=test_assertion.cached_badgeclass.entity_id,
            assertion=test_assertion.entity_id
        ), updated_data)
        self.assertEqual(response.status_code, 200)
        updated_assertion = BadgeInstance.objects.get(entity_id=test_assertion.entity_id)
        updated_obo = json.loads(str(unbake(updated_assertion.image)))
        self.assertEqual(updated_obo.get('expires', None), updated_data.get('expires'))

        # v2 api
        v2_backdate = datetime.datetime(year=2002, month=3, day=3, tzinfo=pytz.UTC)
        updated_data = dict(
            issuedOn=v2_backdate.isoformat()
        )

        response = self.client.put('/v2/assertions/{assertion}'.format(
            assertion=test_assertion.entity_id
        ), updated_data)
        self.assertEqual(response.status_code, 200)
        updated_assertion = BadgeInstance.objects.get(entity_id=test_assertion.entity_id)
        updated_obo = json.loads(str(unbake(updated_assertion.image)))
        self.assertEqual(updated_obo.get('issuedOn', None), updated_data.get('issuedOn'))

    #@unittest.skip('For debug speedup')
    def test_can_update_assertion(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data),
            content_type='application/json')

        self.assertEqual(response.status_code, 201)
        original_assertion = response.data

        new_assertion_data = {
            "recipient_type": "id",
            "recipient_identifier": "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18",
            "narrative": "test narrative",
            "evidence_items": [{
                "narrative": "This is the evidence item narrative AGAIN!.",
                "evidence_url": ""
            }],
        }
        response = self.client.put('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=original_assertion.get('slug'),
        ), json.dumps(new_assertion_data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        updated_assertion = response.data
        self.assertDictContainsSubset(new_assertion_data, updated_assertion)

        # verify v2 api
        v2_assertion_data = {
            "evidence": [
                {
                    "narrative": "remove and add new narrative",
                }
            ]
        }
        response = self.client.put('/v2/assertions/{assertion}'.format(
            assertion=original_assertion.get('slug')
        ), json.dumps(v2_assertion_data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        v2_assertion = data.get('result', [None])[0]
        self.assertEqual(len(v2_assertion_data['evidence']), 1)
        self.assertEqual(v2_assertion['evidence'][0]['narrative'], v2_assertion_data['evidence'][0]['narrative'])

        instance = BadgeInstance.objects.get(entity_id=original_assertion['slug'])
        image = instance.image
        image_data = json.loads(unbake(image))

        self.assertEqual(image_data.get('evidence', {})[0].get('narrative'), v2_assertion_data['evidence'][0]['narrative'])

    #@unittest.skip('For debug speedup')
    def test_can_issue_assertion_with_expiration(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)
        expiration = timezone.now()
        assertion_post_data["expires"] = expiration.isoformat()

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data),
            content_type='application/json')

        self.assertEqual(response.status_code, 201)
        assertion_json = response.data
        self.assertEqual(dateutil.parser.parse(assertion_json.get('expires')), expiration)

        # v1 endpoint returns expiration
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=assertion_json.get('slug')
        ))
        self.assertEqual(response.status_code, 200)
        v1_json = response.data
        self.assertEqual(dateutil.parser.parse(v1_json.get('expires')), expiration)

        # v2 endpoint returns expiration
        response = self.client.get('/v2/assertions/{assertion}'.format(
            assertion=assertion_json.get('slug')
        ))
        self.assertEqual(response.status_code, 200)
        v2_json = response.data.get('result')[0]
        self.assertEqual(dateutil.parser.parse(v2_json.get('expires')), expiration)

        # public url returns expiration
        response = self.client.get(assertion_json.get('public_url'))
        self.assertEqual(response.status_code, 200)
        public_json = response.data
        self.assertEqual(dateutil.parser.parse(public_json.get('expires')), expiration)

    #@unittest.skip('For debug speedup')
    def test_can_issue_badge_if_authenticated(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data),
            content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertIn('slug', response.data)
        assertion_slug = response.data.get('slug')

        # assert that the BadgeInstance was published to and fetched from cache
        # query_count = 1 if apps.is_installed('badgebook') else 0
        # with self.assertNumQueries(query_count):
        #     response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
        #         issuer=test_issuer.entity_id,
        #         badge=test_badgeclass.entity_id,
        #         assertion=assertion_slug))
        #     self.assertEqual(response.status_code, 200)

    #@unittest.skip('For debug speedup')
    def test_issue_badge_with_ob1_evidence(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        evidence_url = "http://fake.evidence.url.test"

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        assertion_post_data["evidence"] = evidence_url

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ),  json.dumps(assertion_post_data), content_type='application/json')

        self.assertEqual(response.status_code, 201)

        self.assertIn('slug', response.data)
        assertion_slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=assertion_slug))
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get('json'))
        self.assertEqual(response.data.get('json').get('evidence'), evidence_url)

        # ob2.0 evidence_items also present
        self.assertEqual(response.data.get('evidence_items'), [
            {
                'evidence_url': evidence_url,
                'narrative': None,
            }
        ])

    #@unittest.skip('For debug speedup')
    def test_issue_badge_with_ob2_multiple_evidence(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        evidence_items = [
            {
                'evidence_url': "http://fake.evidence.url.test",
            },
            {
                'evidence_url': "http://second.evidence.url.test",
                "narrative": "some description of how second evidence was collected"
            }
        ]

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)
        assertion_post_data["evidence_items"] = evidence_items

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        assertion_slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=assertion_slug))
        self.assertEqual(response.status_code, 200)
        assertion = response.data

        fetched_evidence_items = assertion.get('evidence_items')
        self.assertEqual(len(fetched_evidence_items), len(evidence_items))
        for i in range(0,len(evidence_items)):
            self.assertEqual(fetched_evidence_items[i].get('url'), evidence_items[i].get('url'))
            self.assertEqual(fetched_evidence_items[i].get('narrative'), evidence_items[i].get('narrative'))

        # ob1.0 evidence url also present
        self.assertIsNotNone(assertion.get('json'))
        assertion_public_url = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={'entity_id': assertion_slug})
        self.assertEqual(assertion.get('json').get('evidence'), assertion_public_url)

    # we dont use V2
    # def test_v2_issue_with_evidence(self):
    #     test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
    #     test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
    #     test_user = self.setup_user(authenticate=True, teacher=True)
    #     test_issuer = self.setup_issuer(owner=test_user)
    #     test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
    #
    #
    #     evidence_items = [
    #         {
    #             'url': "http://fake.evidence.url.test",
    #         },
    #         {
    #             'url': "http://second.evidence.url.test",
    #             "narrative": "some description of how second evidence was collected"
    #         }
    #     ]
    #
    #     assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)
    #     assertion_post_data["evidence"] = evidence_items
    #
    #
    #     response = self.client.post('/v2/badgeclasses/{badge}/assertions'.format(
    #         badge=test_badgeclass.entity_id
    #     ), json.dumps(assertion_post_data), content_type='application/json')
    #
    #     self.assertEqual(response.status_code, 201)
    #
    #     assertion_slug = response.data['result'][0]['entityId']
    #     response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
    #         issuer=test_issuer.entity_id,
    #         badge=test_badgeclass.entity_id,
    #         assertion=assertion_slug))
    #     self.assertEqual(response.status_code, 200)
    #     assertion = response.data
    #
    #     v2_json = self.client.get('/public/assertions/{}?v=2_0'.format(assertion_slug), format='json').data
    #
    #     fetched_evidence_items = assertion.get('evidence_items')
    #     self.assertEqual(len(fetched_evidence_items), len(evidence_items))
    #     for i in range(0, len(evidence_items)):
    #         self.assertEqual(v2_json['evidence'][i].get('id'), evidence_items[i].get('url'))
    #         self.assertEqual(v2_json['evidence'][i].get('narrative'), evidence_items[i].get('narrative'))
    #         self.assertEqual(fetched_evidence_items[i].get('evidence_url'), evidence_items[i].get('url'))
    #         self.assertEqual(fetched_evidence_items[i].get('narrative'), evidence_items[i].get('narrative'))
    #
    #     # ob1.0 evidence url also present
    #     self.assertIsNotNone(assertion.get('json'))
    #     assertion_public_url = OriginSetting.HTTP + reverse('badgeinstance_json', kwargs={'entity_id': assertion_slug})
    #     self.assertEqual(assertion.get('json').get('evidence'), assertion_public_url)

    #@unittest.skip('For debug speedup')
    def test_issue_badge_with_ob2_one_evidence_item(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        evidence_items = [
            {
                'narrative': "Executed some sweet skateboard tricks that made us completely forget the badge criteria"
            }
        ]

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)
        assertion_post_data["evidence_items"] = evidence_items

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertEqual(response.status_code, 201)

        assertion_slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=assertion_slug))
        self.assertEqual(response.status_code, 200)
        assertion = response.data

        v2_json = self.client.get('/public/assertions/{}?v=2_0'.format(assertion_slug), format='json').data

        fetched_evidence_items = assertion.get('evidence_items')
        self.assertEqual(len(fetched_evidence_items), len(evidence_items))
        for i in range(0,len(evidence_items)):
            self.assertEqual(v2_json['evidence'][i].get('id'), evidence_items[i].get('url'))
            self.assertEqual(v2_json['evidence'][i].get('narrative'), evidence_items[i].get('narrative'))
            self.assertEqual(fetched_evidence_items[i].get('url'), evidence_items[i].get('url'))
            self.assertEqual(fetched_evidence_items[i].get('narrative'), evidence_items[i].get('narrative'))

        # ob1.0 evidence url also present
        self.assertIsNotNone(assertion.get('json'))
        assertion_public_url = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={'entity_id': assertion_slug})
        self.assertEqual(assertion.get('json').get('evidence'), assertion_public_url)

    #@unittest.skip('For debug speedup')
    def test_resized_png_image_baked_properly(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)


        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertIn('slug', response.data)
        assertion_slug = response.data.get('slug')

        instance = BadgeInstance.objects.get(entity_id=assertion_slug)

        instance.image.open()
        self.assertIsNotNone(unbake(instance.image))
        instance.image.close()
        instance.image.open()

        image_data_present = False
        badge_data_present = False
        reader = png.Reader(file=instance.image)
        for chunk in reader.chunks():
            if chunk[0] == 'IDAT':
                image_data_present = True
            elif chunk[0] == 'iTXt' and chunk[1].startswith('openbadges\x00\x00\x00\x00\x00'):
                badge_data_present = True

        self.assertTrue(image_data_present and badge_data_present)

    #@unittest.skip('For debug speedup')
    def test_authenticated_editor_can_issue_badge(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=False, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        editor_user = self.setup_user(authenticate=True, teacher=True, surfconext_id='somerandomid')
        IssuerStaff.objects.create(
            issuer=test_issuer,
            role=IssuerStaff.ROLE_EDITOR,
            user=editor_user
        )

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data),
            content_type='application/json')
        self.assertEqual(response.status_code, 201)

    #@unittest.skip('For debug speedup')
    def test_authenticated_nonowner_user_cant_issue(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=False, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        non_editor_user = self.setup_user(authenticate=True, teacher=True, surfconext_id='somerandomid')

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertEqual(response.status_code, 404)

    #@unittest.skip('For debug speedup')
    def test_unauthenticated_user_cant_issue(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=False, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertIn(response.status_code, (401, 403, 404))

    #@unittest.skip('For debug speedup')
    def test_issue_assertion_with_notify(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    #@unittest.skip('For debug speedup')
    def test_first_assertion_always_notifies_recipient(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        outbox_count = len(mail.outbox)

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), outbox_count+1)

        # should not get notified of second assertion
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), outbox_count+1)

    #@unittest.skip('For debug speedup')
    def test_authenticated_owner_list_assertions(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_badgeclass.issue(recipient_id='new.recipient@email.test')
        test_badgeclass.issue(recipient_id='second.recipient@email.test')

        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    #@unittest.skip('For debug speedup')
    def test_issuer_instance_list_assertions(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_badgeclass.issue(recipient_id='new.recipient@email.test')
        test_badgeclass.issue(recipient_id='second.recipient@email.test')

        response = self.client.get('/v1/issuer/issuers/{issuer}/assertions'.format(
            issuer=test_issuer.entity_id,
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    #@unittest.skip('For debug speedup')
    def test_issuer_instance_list_assertions_with_id(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_badgeclass.issue(recipient_id='new.recipient@email.test')
        test_badgeclass.issue(recipient_id='second.recipient@email.test')

        response = self.client.get('/v1/issuer/issuers/{issuer}/assertions?recipient=new.recipient@email.test'.format(
            issuer=test_issuer.entity_id,
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    #@unittest.skip('For debug speedup')
    def test_can_revoke_assertion(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        revocation_reason = 'Earner kind of sucked, after all.'

        response = self.client.delete('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=test_assertion.entity_id,
        ), {'revocation_reason': revocation_reason })
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/public/assertions/{assertion}.json'.format(assertion=test_assertion.entity_id))
        self.assertEqual(response.status_code, 200)
        assertion_obo = json.loads(response.content)
        self.assertDictContainsSubset(dict(
            revocationReason=revocation_reason,
            revoked=True
        ), assertion_obo)

    #@unittest.skip('For debug speedup')
    def test_cannot_revoke_assertion_if_missing_reason(self):
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        response = self.client.delete('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=test_assertion.entity_id,
        ))
        self.assertEqual(response.status_code, 400)

    #@unittest.skip('For debug speedup')
    def test_issue_svg_badge(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        with open(self.get_test_svg_image_path(), 'r') as svg_badge_image:
            response = self.client.post('/v1/issuer/issuers/{issuer}/badges'.format(
                issuer=test_issuer.entity_id,
            ), {
                'name': 'svg badge',
                'description': 'svg badge',
                'image': svg_badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            })
            badgeclass_slug = response.data.get('slug')

        test_badgeclass = BadgeClass.objects.get(entity_id=badgeclass_slug)
        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=badgeclass_slug
        ), json.dumps(assertion_post_data), content_type='application/json')
        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=badgeclass_slug,
            assertion=slug
        ))
        self.assertEqual(response.status_code, 200)

    #@unittest.skip('For debug speedup')
    def test_new_assertion_updates_cached_user_badgeclasses(self):
        test_eduid = "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18"
        test_recipient = self.setup_user(authenticate=True, eduid=test_eduid)
        test_user = self.setup_user(authenticate=True, teacher=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        original_recipient_count = test_badgeclass.recipient_count()

        assertion_post_data = self.enroll_user(test_recipient, test_badgeclass)

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), json.dumps(assertion_post_data), content_type='application/json')

        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ))
        badgeclass_data = response.data
        self.assertEqual(badgeclass_data.get('recipient_count'), original_recipient_count+1)

    # def test_batch_assertions_throws_400(self):
    #     test_user = self.setup_user(authenticate=True)
    #     test_issuer = self.setup_issuer(owner=test_user)
    #     test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
    #     invalid_batch_assertion_props = [
    #         {
    #             "recipient": {
    #                 "identity": "foo@bar.com"
    #             }
    #         }
    #     ]
    #     response = self.client.post('/v2/badgeclasses/{badge}/issue'.format(
    #         badge=test_badgeclass.entity_id
    #     ), invalid_batch_assertion_props, format='json')
    #     self.assertEqual(response.status_code, 400)

    # def test_batch_assertions_with_invalid_issuedon(self):
    #     test_user = self.setup_user(authenticate=True)
    #     test_issuer = self.setup_issuer(owner=test_user)
    #     test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
    #     invalid_batch_assertion_props = {
    #         "assertions": [
    #             {
    #                 'recipient': {
    #                     "identity": "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18",
    #                     "type": "id",
    #                 }
    #             },
    #             {
    #                 'recipient': {
    #                     "identity": "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18",
    #                     "type": "id",
    #                 },
    #                 'issuedOn': 1512151153620
    #             },
    #         ]
    #     }
    #     response = self.client.post('/v2/badgeclasses/{badge}/issue'.format(
    #         badge=test_badgeclass.entity_id
    #     ), invalid_batch_assertion_props, format='json')
    #     self.assertEqual(response.status_code, 400)

    # def test_batch_assertions_with_evidence(self):
    #     test_user = self.setup_user(authenticate=True)
    #     test_issuer = self.setup_issuer(owner=test_user)
    #     test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
    #
    #     batch_assertion_props = {
    #         'assertions': [{
    #             "recipient": {
    #                 "identity": "urn:mace:eduid.nl:1.0:d57b4355-c7c6-4924-a944-6172e31e9bbc:27871c14-b952-4d7e-85fd-6329ac5c6f18",
    #                 "type": "id",
    #                 "hashed": True,
    #             },
    #             "narrative": "foo@bar's test narrative",
    #             "evidence": [
    #                 {
    #                     "url": "http://google.com?evidence=foo.bar",
    #                 },
    #                 {
    #                     "url": "http://google.com?evidence=bar.baz",
    #                     "narrative": "barbaz"
    #                 }
    #             ]
    #         }],
    #         'create_notification': True
    #     }
    #     response = self.client.post('/v2/badgeclasses/{badge}/issue'.format(
    #         badge=test_badgeclass.entity_id
    #     ), batch_assertion_props, format='json')
    #     self.assertEqual(response.status_code, 201)
    #
    #     result = json.loads(response.content)
    #     returned_assertions = result.get('result')
    #
    #     # verify results contain same evidence that was provided
    #     for i in range(0, len(returned_assertions)):
    #         expected = batch_assertion_props['assertions'][i]
    #         self.assertListOfDictsContainsSubset(expected.get('evidence'), returned_assertions[i].get('evidence'))
    #
    #     # verify OBO returns same results
    #     assertion_entity_id = returned_assertions[0].get('entityId')
    #     expected = batch_assertion_props['assertions'][0]
    #
    #     response = self.client.get('/public/assertions/{assertion}.json?v=2_0'.format(
    #         assertion=assertion_entity_id
    #     ), format='json')
    #     self.assertEqual(response.status_code, 200)
    #
    #     assertion_obo = json.loads(response.content)
    #
    #     expected = expected.get('evidence')
    #     evidence = assertion_obo.get('evidence')
    #     for i in range(0, len(expected)):
    #         self.assertEqual(evidence[i].get('id'), expected[i].get('url'))
    #         self.assertEqual(evidence[i].get('narrative', None), expected[i].get('narrative', None))

    def assertListOfDictsContainsSubset(self, expected, actual):
        for i in range(0, len(expected)):
            a = expected[i]
            b = actual[i]
            self.assertDictContainsSubset(a, b)

# we don't use v2 urls
# class V2ApiAssertionTests(SetupIssuerHelper, BadgrTestCase):
#     def test_v2_issue_by_badgeclassOpenBadgeId(self):
#         test_user = self.setup_user(authenticate=True)
#         test_issuer = self.setup_issuer(owner=test_user)
#         test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
#
#         new_assertion_props = {
#             'recipient': {
#                 'identity': 'test3@example.com'
#             },
#             'badgeclassOpenBadgeId': test_badgeclass.jsonld_id
#         }
#         response = self.client.post('/v2/issuers/{issuer}/assertions'.format(
#             issuer=test_issuer.entity_id
#         ), new_assertion_props, format='json')
#         self.assertEqual(response.status_code, 201)
#
#     def test_v2_issue_by_badgeclassOpenBadgeId_permissions(self):
#         test_user = self.setup_user(authenticate=True)
#         test_issuer = self.setup_issuer(owner=test_user)
#
#         other_user = self.setup_user(authenticate=False)
#         other_issuer = self.setup_issuer(owner=other_user)
#         other_badgeclass = self.setup_badgeclass(issuer=other_issuer)
#
#         new_assertion_props = {
#             'recipient': {
#                 'identity': 'test3@example.com'
#             },
#             'badgeclassOpenBadgeId': other_badgeclass.jsonld_id
#         }
#         response = self.client.post('/v2/issuers/{issuer}/assertions'.format(
#             issuer=test_issuer.entity_id
#         ), new_assertion_props, format='json')
#         self.assertEqual(response.status_code, 400)
#
#     def test_v2_issue_entity_id_in_path(self):
#         test_user = self.setup_user(authenticate=True)
#         test_issuer = self.setup_issuer(owner=test_user)
#         test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
#
#         new_assertion_props = {
#             'recipient': {
#                 'identity': 'test3@example.com'
#             }
#         }
#         response = self.client.post('/v2/badgeclasses/{badgeclass}/assertions'.format(
#             badgeclass=test_badgeclass.entity_id), new_assertion_props, format='json')
#         self.assertEqual(response.status_code, 201)
#
#         other_user = self.setup_user(authenticate=False)
#         other_issuer = self.setup_issuer(owner=other_user)
#         other_badgeclass = self.setup_badgeclass(issuer=other_issuer)
#
#         response = self.client.post('/v2/badgeclasses/{badgeclass}/assertions'.format(
#             badgeclass=other_badgeclass.entity_id), new_assertion_props, format='json')
#         self.assertEqual(response.status_code, 404)
