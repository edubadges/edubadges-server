import json

from django.contrib.auth import get_user_model

import responses
from rest_framework.test import APITestCase


from integrity_verifier.testfiles.test_components import test_components


def setup_basic_1_0():
    responses.add(
        responses.GET, 'http://a.com/instance',
        body=test_components['1_0_basic_instance'],
        status=200, content_type='application/json'
    )
    responses.add(
        responses.GET, 'http://a.com/badgeclass',
        body=test_components['1_0_basic_badgeclass'],
        status=200, content_type='application/json'
    )
    responses.add(
        responses.GET, 'http://a.com/issuer',
        body=test_components['1_0_basic_issuer'],
        status=200, content_type='application/json'
    )


class TestSuccessfulBadgeUploads(APITestCase):
    fixtures = ['0001_initial_superuser']

    @responses.activate
    def test_basic_1_0_badge(self):
        setup_basic_1_0()

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
        self.assertEqual(get_response.data[0].get('errors'), [])


class TestCollectionOperations(APITestCase):
    pass