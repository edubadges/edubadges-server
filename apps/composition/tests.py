import json
import os

from django.contrib.auth import get_user_model

import responses
from rest_framework.test import APITestCase

from .models import LocalBadgeClass, LocalIssuer

dir = os.path.dirname(__file__)


def setup_basic_1_0(**kwargs):
    responses.add(
        responses.GET, 'http://a.com/instance',
        body=open(os.path.join(dir, 'testfiles/1_0_basic_instance.json')).read(),
        status=200, content_type='application/json'
    )
    responses.add(
        responses.GET, 'http://a.com/badgeclass',
        body=open(os.path.join(dir, 'testfiles/1_0_basic_badgeclass.json')).read(),
        status=200, content_type='application/json'
    )
    if not kwargs or not 'http://a.com/issuer' in kwargs.get('exclude'):
        responses.add(
            responses.GET, 'http://a.com/issuer',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_issuer.json')).read(),
            status=200, content_type='application/json'
        )
    if not kwargs or not 'http://a.com/badgeclass_image' in kwargs.get('exclude'):
        responses.add(
            responses.GET, 'http://a.com/badgeclass_image',
            body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
            status=200, content_type='image/png'
        )

def setup_resources(resources):
    for item in resources:
        response_body = item.get(
            'response_body',
            open(os.path.join(dir, 'testfiles', item['filename'])).read()
        )
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


class TestBadgeUploads(APITestCase):
    fixtures = ['0001_initial_superuser']

    @responses.activate
    def test_submit_basic_1_0_badge_via_url(self):
        setup_basic_1_0()

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_from_image_url_baked_w_assertion(self):
        setup_basic_1_0()

        responses.add(
            responses.GET, 'http://a.com/baked_image',
            body=open(os.path.join(dir, 'testfiles/baked_image.png')).read(),
            status=200, content_type='image/png'
        )

        post_input = {
            'url': 'http://a.com/baked_image'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )


    @responses.activate
    def test_submit_basic_1_0_badge_image_png(self):
        setup_basic_1_0()

        image = open(os.path.join(dir, 'testfiles/baked_image.png'))
        post_input = {
            'image': image
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_assertion(self):
        setup_basic_1_0()

        post_input = {
            'assertion': open(os.path.join(dir, 'testfiles/1_0_basic_instance.json')).read()
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 201)
        get_response = self.client.get('/v1/earner/badges')
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_with_inaccessible_badge_image(self):
        setup_basic_1_0(**{'exclude': 'http://a.com/badgeclass_image'})

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data[0].startswith('Error retrieving image'))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_issuer(self):
        setup_basic_1_0(**{'exclude': 'http://a.com/issuer'})

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data[0].startswith('Error attempting'))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_badge_prop(self):
        responses.add(
            responses.GET, 'http://a.com/instance',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_instance_missing_badge_prop.json')).read(),
            status=200, content_type='application/json'
        )

        post_input = {
            'url': 'http://a.com/instance'
        }

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data[0], u'Badge components not well formed. Missing structure: badge')

    @responses.activate
    def test_submit_basic_0_5_0_badge_via_url(self):
        setup_basic_0_5_0()

        post_input = {
            'url': 'http://oldstyle.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            response.data[0].startswith("Sorry, v0.5 badges are not supported"))

        # TODO: reimplement if we decide to accept 0.5 badges in the composer
        # get_response = self.client.get('/v1/earner/badges')
        # self.assertEqual(get_response.status_code, 200)
        # self.assertEqual(
        #     get_response.data[0].get('json', {}).get('id'),
        #     'http://oldstyle.com/instance'
        # )

    @responses.activate
    def test_submit_0_5_badge_upload_by_assertion(self):
        setup_basic_0_5_0()

        post_input = {
            'assertion': open(os.path.join(dir, 'testfiles', '0_5_basic_instance.json')).read()
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

    @responses.activate
    def test_creating_no_duplicate_badgeclasses_and_issuers(self):
        setup_basic_1_0()
        setup_resources([
            {'url': 'http://a.com/instance2', 'filename': '1_0_basic_instance2.json'}
        ])

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
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

        self.assertEqual(LocalBadgeClass.objects.all().count(), 1)
        self.assertEqual(LocalIssuer.objects.all().count(), 1)

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

    @responses.activate
    def test_submit_badge_assertion_with_bad_date(self):
        setup_basic_1_0()
        setup_resources([
            {'url': 'http://a.com/instancebaddate',
             'filename': '1_0_basic_instance_with_bad_date.json'}
        ])

        post_input = {
            'url': 'http://a.com/instancebaddate'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

        self.assertTrue(response.data['details']['instance']['BadgeInstanceSerializerV1_0']['issuedOn'][0]
                        .startswith('Invalid format'))

class TestCollectionOperations(APITestCase):
    pass
