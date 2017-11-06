# encoding: utf-8
from __future__ import unicode_literals

import png
from django.apps import apps
from django.core import mail
from django.core.urlresolvers import reverse
from mainsite.tests import BadgrTestCase, SetupIssuerHelper
from openbadges_bakery import unbake

from issuer.models import BadgeInstance, IssuerStaff
from mainsite.utils import OriginSetting


class AssertionTests(SetupIssuerHelper, BadgrTestCase):

    def test_can_issue_badge_if_authenticated(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion = {
            "email": "test@example.com",
            "create_notification": False
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), assertion)
        self.assertEqual(response.status_code, 201)
        self.assertIn('slug', response.data)
        assertion_slug = response.data.get('slug')

        # Assert mail not sent if "create_notification" param included but set to false
        self.assertEqual(len(mail.outbox), 0)

        # assert that the BadgeInstance was published to and fetched from cache
        query_count = 1 if apps.is_installed('badgebook') else 0
        with self.assertNumQueries(query_count):
            response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
                issuer=test_issuer.entity_id,
                badge=test_badgeclass.entity_id,
                assertion=assertion_slug))
            self.assertEqual(response.status_code, 200)

    def test_issue_badge_with_ob1_evidence(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        evidence_url = "http://fake.evidence.url.test"
        assertion = {
            "email": "test@example.com",
            "create_notification": False,
            "evidence": evidence_url
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), assertion)
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

    def test_issue_badge_with_ob2_multiple_evidence(self):
        test_user = self.setup_user(authenticate=True)
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
        assertion_args = {
            "email": "test@example.com",
            "create_notification": False,
            "evidence_items": evidence_items
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), assertion_args, format='json')
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

    def test_resized_png_image_baked_properly(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion = {
            "email": "test@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ), assertion)
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

    def test_authenticated_editor_can_issue_badge(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        editor_user = self.setup_user(authenticate=True)
        IssuerStaff.objects.create(
            issuer=test_issuer,
            role=IssuerStaff.ROLE_EDITOR,
            user=editor_user
        )

        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), {"email": "test@example.com"})
        self.assertEqual(response.status_code, 201)

    def test_authenticated_nonowner_user_cant_issue(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        non_editor_user = self.setup_user(authenticate=True)
        assertion = {
            "email": "test2@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), assertion)

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cant_issue(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion = {
            "email": "test2@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), assertion)
        self.assertEqual(response.status_code, 401)

    def test_issue_assertion_with_notify(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        assertion = {
            "email": "ottonomy@gmail.com",
            'create_notification': True
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), assertion)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

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

        response = self.client.get('/public/assertions/{assertion}'.format(assertion=test_assertion.entity_id))
        self.assertEqual(response.status_code, 410)

    def test_cannot_revoke_assertion_if_missing_reason(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        test_assertion = test_badgeclass.issue(recipient_id='new.recipient@email.test')

        response = self.client.delete('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
            assertion=test_assertion.entity_id,
        ))
        self.assertEqual(response.status_code, 400)

    def test_issue_svg_badge(self):
        test_user = self.setup_user(authenticate=True)
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

        assertion = {
            "email": "test@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=badgeclass_slug
        ), assertion)
        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions/{assertion}'.format(
            issuer=test_issuer.entity_id,
            badge=badgeclass_slug,
            assertion=slug
        ))
        self.assertEqual(response.status_code, 200)

    def test_new_assertion_updates_cached_user_badgeclasses(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        original_recipient_count = test_badgeclass.recipient_count()

        new_assertion_props = {
            'email': 'test3@example.com',
        }
        response = self.client.post('/v1/issuer/issuers/{issuer}/badges/{badge}/assertions'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ), new_assertion_props)
        self.assertEqual(response.status_code, 201)

        response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id,
        ))
        badgeclass_data = response.data
        self.assertEqual(badgeclass_data.get('recipient_count'), original_recipient_count+1)

    def test_batch_assertions_throws_400(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)
        invalid_batch_assertion_props = [
            {
                "recipient": {
                    "identity": "foo@bar.com"
                }
            }
        ]
        response = self.client.post('/v2/badgeclasses/{badge}/issue'.format(
            badge=test_badgeclass.entity_id
        ), invalid_batch_assertion_props, format='json')
        self.assertEqual(response.status_code, 400)



