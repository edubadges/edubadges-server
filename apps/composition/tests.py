import base64

import os
import responses
from django.contrib.auth import get_user_model

from badgeuser.models import CachedEmailAddress, BadgeUser
from composition.models import (LocalBadgeInstance,
                                Collection, LocalBadgeInstanceCollection, )
from composition.serializers import (CollectionSerializer, )
from issuer.models import BadgeClass, Issuer
from mainsite.tests.base import BadgrTestCase

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


class TestBadgeUploads(BadgrTestCase):

    def setup_user(self, email='test@example.com', authenticate=True):
        user, _ = BadgeUser.objects.get_or_create(email=email)
        CachedEmailAddress.objects.create(user=user, email=email, verified=True, primary=True)
        if authenticate:
            self.client.force_authenticate(user=user)
        return user

    @responses.activate
    def test_submit_basic_1_0_badge_via_url(self):
        setup_basic_1_0()
        self.setup_user()

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
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

        new_instance = LocalBadgeInstance.objects.first()
        self.assertEqual(get_response.data[0].get('json', {}).get('image', {}).get('id'), new_instance.image_url())

    @responses.activate
    def test_submit_basic_1_0_badge_via_url_plain_json(self):
        setup_basic_1_0()
        self.setup_user()

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
        self.setup_user(email='not.test@email.example.com')

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data[0],
            'The badge you are trying to import does not belong to one of your verified e-mail addresses.'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_from_image_url_baked_w_assertion(self):
        setup_basic_1_0()
        self.setup_user()

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
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )


    @responses.activate
    def test_submit_basic_1_0_badge_image_png(self):
        setup_basic_1_0()
        self.setup_user()

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
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_image_datauri_png(self):
        setup_basic_1_0()
        self.setup_user()

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
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_assertion(self):
        setup_basic_1_0()
        self.setup_user()

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
            get_response.data[0].get('json', {}).get('id'),
            'http://a.com/instance'
        )

    @responses.activate
    def test_submit_basic_1_0_badge_url_variant_email(self):
        setup_basic_1_0(**{'exclude': 'http://a.com/instance'})
        setup_resources([
            {'url': 'http://a.com/instance3', 'filename': '1_0_basic_instance3.json'}
        ])
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instance3',
            'recipient_identifier': "TEST@example.com"
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
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data[0].startswith('Error retrieving image'))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_issuer(self):
        setup_basic_1_0(**{'exclude': ['http://a.com/issuer']})
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.data[0].startswith('Error attempting'))

    @responses.activate
    def test_submit_basic_1_0_badge_missing_badge_prop(self):
        self.setup_user()

        responses.add(
            responses.GET, 'http://a.com/instance',
            body=open(os.path.join(dir, 'testfiles/1_0_basic_instance_missing_badge_prop.json')).read(),
            status=200, content_type='application/json'
        )

        post_input = {
            'url': 'http://a.com/instance'
        }

        response = self.client.post(
            '/v1/earner/badges', post_input
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data[0], u'Badge components not well formed. Missing structure: badge')

    @responses.activate
    def test_submit_basic_0_5_0_badge_via_url(self):
        setup_basic_0_5_0()
        self.setup_user()

        post_input = {
            'url': 'http://oldstyle.com/instance'
        }
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
        self.setup_user()

        post_input = {
            'assertion': open(os.path.join(dir, 'testfiles', '0_5_basic_instance.json')).read()
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

    @responses.activate
    def test_creating_no_duplicate_badgeclasses_and_issuers(self):
        setup_basic_1_0()
        self.setup_user()
        setup_resources([
            {'url': 'http://a.com/instance2', 'filename': '1_0_basic_instance2.json'}
        ])

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

        self.assertEqual(BadgeClass.objects.all().count(), 1)
        self.assertEqual(Issuer.objects.all().count(), 1)

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
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instancebaddate'
        }
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
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instance'
        }
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
        self.setup_user()

        post_input = {
            'url': 'http://a.com/instance'
        }
        response = self.client.post(
            '/v1/earner/badges', post_input
        )
        self.assertEqual(response.status_code, 400)

        self.assertTrue(response.data[0].startswith('Unable to get valid baked image or valid json response from'))


class TestCollections(BadgrTestCase):
    def setUp(self):
        super(TestCollections, self).setUp()
        self.user, _ = BadgeUser.objects.get_or_create(email='test@example.com')

        self.cached_email, _ = CachedEmailAddress.objects.get_or_create(user=self.user, email='test@example.com', verified=True, primary=True)

        self.issuer, _ = Issuer.objects.get_or_create(
            name="Open Badges",
            created_at="2015-12-15T15:55:51Z",
            created_by=None,
            slug="open-badges",
            source_url="http://badger.openbadges.org/program/meta/bda68a0b505bc0c7cf21bc7900280ee74845f693",
            source="test-fixture",
            image=""
        )

        self.badge_class, _ = BadgeClass.objects.get_or_create(
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

        self.local_badge_instance_1, _ = LocalBadgeInstance.objects.get_or_create(
            recipient_user=self.user,
            recipient_identifier="test@example.com",
            issuer_badgeclass=self.badge_class,
            created_at="2015-12-15T15:55:51Z",
            created_by=None,
            slug="3949c957-11e2-464d-b1c0-0d4fa645e93a",
            json="{\"issuedOn\":\"2013-10-25T12:55:31\",\"uid\":\"dc8959d7639e64178ec24fb222f11d050528df74\",\"type\":\"Assertion\",\"image\":\"http://localhost:8000/media/uploads/badges/local_badgeinstance_174e70bf-b7a8-4b71-8125-c34d1a994a7c.png\",\"badge\":{\"description\":\"The MozFest 2013 Reveler Badge is special edition badge acknowledging a personal commitment to forging the future of the web during MozFest: working with peers to imagine and build an open future of learning, making, journalism, data, science, privacy, and mobile.\",\"tags\":[],\"image\":\"http://badger.openbadges.org/badge/image/mozfest-reveler.png\",\"criteria\":\"http://badger.openbadges.org/badge/criteria/mozfest-reveler\",\"issuer\":{\"url\":\"http://openbadges.org\",\"type\":\"Issuer\",\"id\":\"http://badger.openbadges.org/program/meta/bda68a0b505bc0c7cf21bc7900280ee74845f693\",\"name\":\"Open Badges\"},\"type\":\"BadgeClass\",\"id\":\"http://badger.openbadges.org/badge/meta/mozfest-reveler\",\"name\":\"MozFest Reveler\"},\"@context\":\"https://w3id.org/openbadges/v1\",\"recipient\":{\"type\":\"email\",\"recipient\":\"test@example.com\"},\"id\":\"http://badger.openbadges.org/badge/assertion/dc8959d7639e64178ec24fb222f11d050528df74\"}",
            revocation_reason=None,
            identifier="http://badger.openbadges.org/badge/assertion/dc8959d7639e64178ec24fb222f11d050528df74",
            image="uploads/badges/local_badgeinstance_174e70bf-b7a8-4b71-8125-c34d1a994a7c.png",
            revoked=False
        )

        self.local_badge_instance_2, _ = LocalBadgeInstance.objects.get_or_create(
            recipient_user=self.user,
            recipient_identifier="test@example.com",
            issuer_badgeclass=self.badge_class,
            created_at="2015-12-21T20:41:16Z",
            created_by=None,
            slug="32f81606-4430-40df-a9fc-382a2d1f1574",
            revocation_reason=None,
            identifier="http://badger.openbadges.org/badge/assertion/c14a16d06481ba99fdf82b0b4b12d275c03c76cd",
            image="uploads/badges/local_badgeinstance_bf562e3a-9f26-493e-840f-0ecb31d7bebc.png",
            revoked=False
        )

        self.local_badge_instance_3, _ = LocalBadgeInstance.objects.get_or_create(
            recipient_user=self.user,
            recipient_identifier="test@example.com",
            issuer_badgeclass=self.badge_class,
            created_at="2015-12-28T15:54:50Z",
            created_by=None,
            slug="c36110d9-938a-4052-9a13-ed8424454ed5",
            revocation_reason=None,
            identifier="http://app.achievery.com/badge-assertion/4613999",
            image="uploads/badges/local_badgeinstance_e63cdadc-7cad-46ee-a4d0-a75458678e04.png",
            revoked=False
        )

        self.collection, _ = Collection.objects.get_or_create(
            owner=self.user,
            description='The Freshest Ones',
            name='Fresh Badges',
            slug='fresh-badges'
        )

        Collection.objects.create(
            owner=self.user,
            description='It\'s even fresher.',
            name='Cool New Collection',
            slug='cool-new-collection'
        )
        Collection.objects.create(
            owner=self.user,
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
                {'id': self.local_badge_instance_1.pk},
                {'id': self.local_badge_instance_2.pk, 'description': 'A cool badge'}
            ]
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/v1/earner/collections', data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get('published'))

        self.assertEqual([i['id'] for i in response.data.get('badges')], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])
        self.assertEqual(response.data.get('badges')[1]['description'], 'A cool badge')

    def test_can_define_collection_serializer(self):
        """
        A new collection may be created directly via serializer.
        """
        data = {
            'name': 'Fruity Collection',
            'description': 'Apples and Oranges',
            'badges': [{'id': self.local_badge_instance_1.pk}, {'id': self.local_badge_instance_2.pk, 'description': 'A cool badge'}]
        }

        serializer = CollectionSerializer(data=data, context={'user': self.user})
        serializer.is_valid(raise_exception=True)
        collection = serializer.save()

        self.assertIsNotNone(collection.pk)
        self.assertEqual(collection.name, data['name'])
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual(collection.badges.filter(instance_id=self.local_badge_instance_2.pk).first().description, 'A cool badge')

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

        collection = Collection.objects.get(pk=self.collection.pk)

        self.assertTrue(collection.published)

        response = self.client.delete('/v1/earner/collections/fresh-badges/share')
        self.assertEqual(response.status_code, 204)
        self.assertIsNone(response.data)

        self.assertFalse(self.collection.published)

    def test_can_add_remove_collection_badges_via_serializer(self):
        """
        The CollectionSerializer should be able to update an existing collection's badge list
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        serializer = CollectionSerializer(
            collection,
            data={'badges': [{'id': self.local_badge_instance_1.pk}, {'id': self.local_badge_instance_2.pk}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        serializer = CollectionSerializer(
            collection,
            data={'badges': [{'id': self.local_badge_instance_2.pk}, {'id': self.local_badge_instance_3.pk}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_2.pk, self.local_badge_instance_3.pk])

    def test_can_add_remove_collection_badges_via_collection_detail_api(self):
        """
        A PUT request to the CollectionDetail view should be able to update the list of badges
        in a collection.
        """
        collection = Collection.objects.first()
        self.assertEqual(collection.badges.count(), 0)

        data = {
            'badges': [{'id': self.local_badge_instance_1.pk}, {'id': self.local_badge_instance_2.pk}],
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
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        data = {'badges': [{'id': self.local_badge_instance_2.pk}, {'id': self.local_badge_instance_3.pk}]}
        response = self.client.put(
            '/v1/earner/collections/{}'.format(collection.slug),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data.get('badges')], [self.local_badge_instance_2.pk, self.local_badge_instance_3.pk])
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_2.pk, self.local_badge_instance_3.pk])

    def test_can_add_remove_badges_via_collection_badge_detail_api(self):
        self.assertEqual(self.collection.badges.count(), 0)

        data = [{'id': self.local_badge_instance_1.pk}, {'id': self.local_badge_instance_2.pk}]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/v1/earner/collections/{}/badges'.format(self.collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

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
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_2.pk])

    def test_can_add_remove_issuer_badges_via_api(self):
        self.assertEqual(self.collection.badges.count(), 0)

        data = [
            {'id': self.local_badge_instance_1.pk},
            {'id': self.local_badge_instance_2.slug}
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/v1/earner/collections/{}/badges'.format(self.collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        self.assertEqual(self.collection.badges.count(), 2)
        self.assertEqual([i.badge_instance.pk for i in self.collection.badges.all()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        response = self.client.get(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.slug, self.local_badge_instance_2.pk)
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.slug, self.local_badge_instance_2.pk)
        )
        self.assertEqual(response.status_code, 204)

    def test_api_handles_null_description_and_adds_badge(self):
        self.assertEqual(self.collection.badges.count(), 0)

        data = {'badges': [{'id': self.local_badge_instance_1.pk, 'description': None}]}

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}'.format(self.collection.slug), data=data,
            format='json')
        self.assertEqual(response.status_code, 200)

        entry = self.collection.badges.first()
        self.assertEqual(entry.description, '')
        self.assertEqual(entry.instance_id, self.local_badge_instance_1.pk)

    def test_can_add_remove_collection_badges_collection_badgelist_api(self):
        """
        A PUT request to the Collection BadgeList endpoint should update the list of badges
        n a collection
        """
        self.assertEqual(self.collection.badges.count(), 0)

        data = [{'id': self.local_badge_instance_1.pk}, {'id': self.local_badge_instance_2.pk}]

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(self.collection.slug), data=data,
            format='json')

        self.assertEqual(response.status_code, 200)
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_1.pk, self.local_badge_instance_2.pk])

        data = [{'id': self.local_badge_instance_2.pk}, {'id': self.local_badge_instance_3.pk}]
        response = self.client.put(
            '/v1/earner/collections/{}/badges'.format(collection.slug),
            data=data, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([i['id'] for i in response.data], [self.local_badge_instance_2.pk, self.local_badge_instance_3.pk])
        collection = Collection.objects.first()  # reload
        self.assertEqual(collection.badges.count(), 2)
        self.assertEqual([i.instance.pk for i in collection.badges.all()], [self.local_badge_instance_2.pk, self.local_badge_instance_3.pk])

    def test_can_update_badge_description_in_collection_via_detail_api(self):
        self.assertEqual(self.collection.badges.count(), 0)

        serializer = CollectionSerializer(
            self.collection,
            data={'badges': [{'id': self.local_badge_instance_1.pk},
                             {'id': self.local_badge_instance_2.pk}]},
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        self.assertEqual(self.collection.badges.count(), 2)

        self.client.force_authenticate(user=self.user)
        response = self.client.put(
            '/v1/earner/collections/{}/badges/{}'.format(self.collection.slug, self.local_badge_instance_1.pk),
            data={'id': 1, 'description': 'A cool badge.'}, format='json'
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'id': self.local_badge_instance_1.pk, 'description': 'A cool badge.'})

        obj = LocalBadgeInstanceCollection.objects.get(collection=self.collection, instance_id=self.local_badge_instance_1.pk)
        self.assertEqual(obj.description, 'A cool badge.')

    def test_badge_share_json(self):
        """
        Badge Share page returns JSON by default
        """
        response = self.client.get('/share/badge/{}'.format(self.local_badge_instance_1.pk), content_type="application/json")

        self.assertEqual(response.data.get('uid'), u'dc8959d7639e64178ec24fb222f11d050528df74')

    def test_badge_share_html(self):
        """
        Badge Share page returns HTML if requested
        """
        response = self.client.get(
            '/share/badge/{}'.format(self.local_badge_instance_1.pk),
            **{'HTTP_ACCEPT': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
        )

        self.assertContains(response, "<h1>{}</h1>".format(self.local_badge_instance_1.cached_badgeclass.name))
        self.assertContains(response, 'href="http://badger.openbadges.org/badge/assertion/dc8959d7639e64178ec24fb222f11d050528df74.json"')
