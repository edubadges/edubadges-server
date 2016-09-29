import base64
import os

from django.core.cache import cache
from django.contrib.auth import get_user_model

import responses
from rest_framework.test import APITestCase

from composition.models import (LocalBadgeClass, LocalIssuer, LocalBadgeInstance,
                                Collection, LocalBadgeInstanceCollection,)
from composition.serializers import (CollectionSerializer, CollectionBadgeSerializer,)

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

    def setUp(self):
        cache.clear()

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

        new_instance = LocalBadgeInstance.objects.first()
        self.assertEqual(get_response.data[0].get('json', {}).get('image', {}).get('id'), new_instance.image_url())

    @responses.activate
    def test_submit_basic_1_0_badge_via_url_plain_json(self):
        setup_basic_1_0()

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges?json_format=plain', post_input
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data.get('json').get('badge').get('description'),
            u'Basic as it gets. v1.0'
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
    def test_submit_basic_1_0_badge_image_datauri_png(self):
        setup_basic_1_0()

        image = open(os.path.join(dir, 'testfiles/baked_image.png'))
        encoded = 'data:image/png;base64,' + base64.b64encode(image.read())
        post_input = {
            'image': encoded
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input, format='json'
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

    @responses.activate
    def test_submit_badge_invalid_component_json(self):
        setup_basic_1_0(**{'exclude': ['http://a.com/issuer']})
        setup_resources([
            {'url': 'http://a.com/issuer',
             'filename': '1_0_basic_issuer_invalid_json.json'}
        ])

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

        self.assertTrue(response.data[1].startswith('Unable to find a valid json component'))

    @responses.activate
    def test_submit_badge_invalid_assertion_json(self):
        setup_resources([
            {'url': 'http://a.com/instance',
             'filename': '1_0_basic_issuer_invalid_json.json'}
        ])

        post_input = {
            'url': 'http://a.com/instance'
        }
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

        self.assertTrue(response.data[0].startswith('Unable to get valid baked image or valid json response from'))


class TestCollectionOperations(APITestCase):
    fixtures = ['0001_initial_superuser', 'initial_collections', 'initial_my_badges']

    def setUp(self):
        self.user = get_user_model().objects.get(pk=1)

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
            'badges': [{'id': 1}, {'id': 2, 'description': 'A cool badge'}]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/v1/earner/collections', data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('published'))

        self.assertEqual([i['id'] for i in response.data.get('badges')], [1, 2])
        self.assertEqual(response.data.get('badges')[1]['description'], 'A cool badge')

    def test_can_define_collection_serializer(self):
        """
        A new collection may be created directly via serializer.
        """
        data = {
            'name': 'Fruity Collection',
            'description': 'Apples and Oranges',
            'badges': [{'id': 1}, {'id': 2, 'description': 'A cool badge'}]
        }

        serializer = CollectionSerializer(data=data, context={'user': self.user})
        serializer.is_valid(raise_exception=True)
        collection = serializer.save()

        self.assertIsNotNone(collection.pk)
        self.assertEqual(collection.name, data['name'])
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual(collection.badges.filter(instance_id=2).first().description, 'A cool badge')

    def test_can_delete_collection(self):
        """
        Authorized user may delete one of their defined collections.
        """
        collection = Collection.objects.first()

        self.client.force_authenticate(user=self.user)
        response = self.client.delete('/v1/earner/collections/{}'.format(collection.slug))

        self.assertEqual(response.status_code, 204)

    def test_can_publish_unpublish_collection_serializer(self):
        """
        The CollectionSerializer should be able to update/delete a collection's share hash
        via update method.
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.share_url, '')

        serializer = CollectionSerializer(
            collection,
            data={'published': True}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertNotEqual(collection.share_url, '')
        self.assertTrue(collection.published)

        serializer = CollectionSerializer(
            collection,
            data={'published': False}, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertFalse(collection.published)
        self.assertEqual(collection.share_url, '')


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

        collection = Collection.objects.get(pk=1)
        self.assertTrue(collection.published)

        response = self.client.delete('/v1/earner/collections/fresh-badges/share')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)

        collection = Collection.objects.get(pk=1)
        self.assertFalse(collection.published)


    def test_can_add_remove_collection_badges_via_serializer(self):
        """
        The CollectionSerializer should be able to update an existing collection's badge list
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        serializer = CollectionSerializer(
            collection,
            data={'badges': [{'id': 1}, {'id': 2}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [1, 2])

        serializer = CollectionSerializer(
            collection,
            data={'badges': [{'id': 2}, {'id': 3}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [2, 3])


    def test_can_add_remove_collection_badges_via_collection_detail_api(self):
        """
        A PUT request to the CollectionDetail view should be able to update the list of badges
        in a collection.
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        data = {
            'badges': [{'id': 1}, {'id': 2}],
            'name': collection.name,
            'description': collection.description
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}'.format(collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 200)
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [1, 2])

        data = {'badges': [{'id': 2}, {'id': 3}]}
        response = self.client.put(
            '/v1/earner/collections/{}'.format(collection.slug),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data.get('badges')], [2, 3])
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [2, 3])

    def test_can_add_remove_badges_via_collection_badge_detail_api(self):
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        data = [{'id': 1}, {'id': 2}]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/v1/earner/collections/{}/badges'.format(collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i['id'] for i in response.data], [1, 2])

        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.pk for i in collection.badges.all()], [1, 2])

        response = self.client.get('/v1/earner/collections/{}/badges'.format(collection.slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

        response = self.client.delete(
            '/v1/earner/collections/{}/badges/{}'.format(collection.slug, data[0]['id']),
            data=data, format='json')

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 1)
        self.assertEqual([i.pk for i in collection.badges.all()], [2])

    def test_can_add_remove_collection_badges_collection_badgelist_api(self):
        """
        A PUT request to the Collection BadgeList endpoint should update the list of badges
        n a collection
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        data = [{'id': 1}, {'id': 2}]

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 200)
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [1, 2])

        data = [{'id': 2}, {'id': 3}]
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(collection.slug),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data], [2, 3])
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [2, 3])

    def test_can_update_badge_description_in_collection_via_detail_api(self):
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        serializer = CollectionSerializer(
            collection,
            data={'badges': [{'id': 1}, {'id': 2}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.badges.count(), 2)

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges/{}'.format(collection.slug, 1),
            data={'id': 1, 'description': 'A cool badge.'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': 1, 'description': 'A cool badge.'})

        obj = LocalBadgeInstanceCollection.objects.get(collection=collection, instance_id=1)
        self.assertEqual(obj.description, 'A cool badge.')
