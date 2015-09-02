import json
import os

from django.contrib.auth import get_user_model

import responses
from rest_framework.test import APITestCase

dir = os.path.dirname(__file__)


def setup_basic_1_0():
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
    responses.add(
        responses.GET, 'http://a.com/issuer',
        body=open(os.path.join(dir, 'testfiles/1_0_basic_issuer.json')).read(),
        status=200, content_type='application/json'
    )
    responses.add(
        responses.GET, 'http://a.com/badgeclass_image',
        body=open(os.path.join(dir, 'testfiles/unbaked_image.png')).read(),
        status=200, content_type='image/png'
    )


class TestSuccessfulBadgeUploads(APITestCase):
    fixtures = ['0001_initial_superuser']

    @responses.activate
    def test_basic_1_0_badge(self):
        setup_basic_1_0()

        # import pdb; pdb.set_trace()

        post_input = {
            'recipient': 'test@example.com', 'url': 'http://a.com/instance'
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


class TestCollectionOperations(APITestCase):
    pass
