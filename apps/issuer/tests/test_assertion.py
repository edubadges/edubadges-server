# encoding: utf-8
from __future__ import unicode_literals

import os.path
import shutil

import os
import png
from django.apps import apps
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.test import override_settings
from mainsite import TOP_DIR
from openbadges_bakery import unbake
from rest_framework.test import APITestCase

from issuer.models import BadgeClass, BadgeInstance
from issuer.serializers_v1 import BadgeInstanceSerializerV1
from mainsite.utils import OriginSetting


@override_settings(
    CELERY_ALWAYS_EAGER=True,
    SESSION_ENGINE='django.contrib.sessions.backends.cache',
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    }
)
class AssertionTests(APITestCase):
    # fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

    def setUp(self):
        cache.clear()

    def ensure_image_exists(self, badge_object, image_filename='guinea_pig_testing_badge.png'):
        if not os.path.exists(badge_object.image.path):
            shutil.copy2(
                os.path.join(os.path.dirname(__file__), 'testfiles', image_filename),
                badge_object.image.path
            )

    def test_badge_instance_serializer_notification_validation(self):
        data = {
            "email": "test@example.com",
            "create_notification": False
        }

        serializer = BadgeInstanceSerializerV1(data=data)
        serializer.is_valid(raise_exception=True)

        self.assertEqual(serializer.validated_data.get('create_notification'), data['create_notification'])

    def test_authenticated_owner_issue_badge(self):
        # load test image into media files if it doesn't exist
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        assertion = {
            "email": "test@example.com",
            "create_notification": False
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', assertion)

        self.assertEqual(response.status_code, 201)

        # Assert mail not sent if "create_notification" param included but set to false
        self.assertEqual(len(mail.outbox), 0)

        # assert that the BadgeInstance was published to and fetched from cache
        query_count = 1 if apps.is_installed('badgebook') else 0
        with self.assertNumQueries(query_count):
            slug = response.data.get('slug')
            response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions/{}'.format(slug))
            self.assertEqual(response.status_code, 200)

    def test_issue_badge_with_ob1_evidence(self):
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        evidence_url = "http://fake.evidence.url.test"
        assertion = {
            "email": "test@example.com",
            "create_notification": False,
            "evidence": evidence_url
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', assertion)
        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions/{}'.format(slug))
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
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

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
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', assertion_args, format='json')
        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions/{}'.format(slug))
        self.assertEqual(response.status_code, 200)
        assertion = response.data

        fetched_evidence_items = assertion.get('evidence_items')
        self.assertEqual(len(fetched_evidence_items), len(evidence_items))
        for i in range(0,len(evidence_items)):
            self.assertEqual(fetched_evidence_items[i].get('url'), evidence_items[i].get('url'))
            self.assertEqual(fetched_evidence_items[i].get('narrative'), evidence_items[i].get('narrative'))

        # ob1.0 evidence url also present
        self.assertIsNotNone(assertion.get('json'))
        assertion_public_url = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={'slug': slug})
        self.assertEqual(assertion.get('json').get('evidence'), assertion_public_url)

    def test_resized_png_image_baked_properly(self):
        current_user = get_user_model().objects.get(pk=1)
        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            }

            self.client.force_authenticate(user=current_user)
            response_bc = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )

        assertion = {
            "email": "test@example.com"
        }
        self.client.force_authenticate(user=current_user)
        response = self.client.post('/v1/issuer/issuers/test-issuer/badges/badge-of-awesome/assertions', assertion)

        instance = BadgeInstance.objects.get(slug=response.data.get('slug'))

        instance.image.open()
        self.assertIsNotNone(unbake(instance.image))
        instance.image.close()
        instance.image.open()

        reader = png.Reader(file=instance.image)
        for chunk in reader.chunks():
            if chunk[0] == 'IDAT':
                image_data_present = True
            elif chunk[0] == 'iTXt' and chunk[1].startswith('openbadges\x00\x00\x00\x00\x00'):
                badge_data_present = True

        self.assertTrue(image_data_present and badge_data_present)

        # Assert notification not sent if "create_notification" param not included
        self.assertEqual(len(mail.outbox), 0)

    def test_authenticated_editor_can_issue_badge(self):
        # load test image into media files if it doesn't exist
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))

        # This issuer has user 2 among its editors.
        the_editor = get_user_model().objects.get(pk=2)
        self.client.force_authenticate(user=the_editor)
        response = self.client.post(
            '/v1/issuer/issuers/edited-test-issuer/badges/badge-of-edited-testing/assertions',
            {"email": "test@example.com", "create_notification": True}
        )

        self.assertEqual(response.status_code, 201)

        # Assert that mail is sent if "create_notification" is included and set to True.
        self.assertEqual(len(mail.outbox), 1)

    def test_authenticated_nonowner_user_cant_issue(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=2))
        assertion = {
            "email": "test2@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer/badges/badge-of-testing/assertions', assertion)

        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_user_cant_issue(self):
        assertion = {"email": "test@example.com"}
        response = self.client.post('/v1/issuer/issuers/test-issuer/badges', assertion)
        self.assertEqual(response.status_code, 401)

    def test_issue_assertion_with_notify(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        assertion = {
            "email": "ottonomy@gmail.com",
            'create_notification': True
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', assertion)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 1)

    def test_authenticated_owner_list_assertions(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_issuer_instance_list_assertions(self):

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/assertions')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_issuer_instance_list_assertions_with_id(self):

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/assertions?recipient=test@example.com')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_revoke_assertion(self):

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete(
            '/v1/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa',
            {'revocation_reason': 'Earner kind of sucked, after all.'}
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa')
        self.assertEqual(response.status_code, 410)

    def test_revoke_assertion_missing_reason(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete(
            '/v1/issuer/issuers/test-issuer/badges/badge-of-testing/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa',
            {}
        )

        self.assertEqual(response.status_code, 400)

    def test_issue_svg_badge(self):
        # load test image into media files if it doesn't exist
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-svg-testing'), 'test_badgeclass.svg')

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        assertion = {
            "email": "test@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-svg-testing/assertions', assertion)

        self.assertEqual(response.status_code, 201)

        slug = response.data.get('slug')
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges/badge-of-svg-testing/assertions/{}'.format(slug))
        self.assertEqual(response.status_code, 200)

    def test_new_assertion_updates_cached_user_badgeclasses(self):

        user = get_user_model().objects.get(pk=1)

        self.client.force_authenticate(user=user)
        badgelist = self.client.get('/v1/issuer/all-badges')
        badge_data = badgelist.data[0]
        number_of_assertions = badge_data['recipient_count']
        # self.ensure_image_exists(badge, 'test_badgeclass.svg') # replace with that badge's filename

        new_assertion_props = {
            'email': 'test3@example.com',
        }

        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', new_assertion_props)
        self.assertEqual(response.status_code, 201)

        new_badgelist = self.client.get('/v1/issuer/all-badges')
        new_badge_data = new_badgelist.data[0]
        updated_number_of_assertions = new_badge_data['recipient_count']

        self.assertEqual(updated_number_of_assertions, number_of_assertions + 1)



