import json
import os
import os.path
from django.apps import apps
import png
import shutil
import urllib

from django.core import mail
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.test import modify_settings, override_settings

from openbadges_bakery import unbake
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from issuer.api import IssuerList
from issuer.models import Issuer, BadgeClass, BadgeInstance, IssuerStaff
from issuer.serializers import BadgeInstanceSerializer
from mainsite import TOP_DIR


factory = APIRequestFactory()

example_issuer_props = {
    'name': 'Awesome Issuer',
    'description': 'An issuer of awe-inspiring credentials',
    'url': 'http://example.com',
    'email': 'contact@example.org'
}


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
class IssuerTests(APITestCase):
    fixtures = ['0001_initial_superuser', 'test_badge_objects.json']

    def setUp(self):
        cache.clear()

    def test_create_issuer_unauthenticated(self):
        view = IssuerList.as_view()

        request = factory.post(
            '/v1/issuer/issuers',
            json.dumps(example_issuer_props),
            content_type='application/json'
        )

        response = view(request)
        self.assertEqual(response.status_code, 401)

    def test_create_issuer_authenticated(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post('/v1/issuer/issuers', example_issuer_props)

        self.assertEqual(response.status_code, 201)

        # assert that name, description, url, etc are set properly in response badge object
        badge_object = response.data.get('json')
        self.assertEqual(badge_object['url'], example_issuer_props['url'])
        self.assertEqual(badge_object['name'], example_issuer_props['name'])
        self.assertEqual(badge_object['description'], example_issuer_props['description'])
        self.assertEqual(badge_object['email'], example_issuer_props['email'])
        self.assertIsNotNone(badge_object.get('id'))
        self.assertIsNotNone(badge_object.get('@context'))

        # assert that the issuer was published to and fetched from the cache
        with self.assertNumQueries(0):
            slug = response.data.get('slug')
            response = self.client.get('/v1/issuer/issuers/{}'.format(slug))
            self.assertEqual(response.status_code, 200)

    def test_create_issuer_authenticated_unconfirmed_email(self):
        first_user_data = user_data = {
            'first_name': 'NEW Test',
            'last_name': 'User',
            'email': 'unclaimed1@example.com',
            'password': '123456'
        }
        response = self.client.post('/v1/user/profile', user_data)

        first_user = get_user_model().objects.get(first_name='NEW Test')

        self.client.force_authenticate(user=first_user)
        response = self.client.post('/v1/issuer/issuers', example_issuer_props)

        self.assertEqual(response.status_code, 403)

    def test_create_issuer_image_500x300_resizes_to_400x400(self):
        view = IssuerList.as_view()

        with open(os.path.join(os.path.dirname(__file__), 'testfiles',
                               '500x300.png'), 'r') as badge_image:
                issuer_fields_with_image = {
                    'name': 'Awesome Issuer',
                    'description': 'An issuer of awe-inspiring credentials',
                    'url': 'http://example.com',
                    'email': 'contact@example.org',
                    'image': badge_image,
                }

                request = factory.post('/v1/issuer/issuers',
                                       issuer_fields_with_image,
                                       format='multipart')

                force_authenticate(request,
                                   user=get_user_model().objects.get(pk=1))
                response = view(request)
                self.assertEqual(response.status_code, 201)

                badge_object = response.data.get('json')
                derived_slug = badge_object['id'].split('/')[-1]
                new_issuer = Issuer.objects.get(slug=derived_slug)

                image_width, image_height = \
                    get_image_dimensions(new_issuer.image.file)
                self.assertEqual(image_width, 400)
                self.assertEqual(image_height, 400)

    def test_create_issuer_image_450x450_resizes_to_400x400(self):
        view = IssuerList.as_view()

        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', '450x450.png'),
            'r') as badge_image:

                issuer_fields_with_image = {
                    'name': 'Awesome Issuer',
                    'description': 'An issuer of awe-inspiring credentials',
                    'url': 'http://example.com',
                    'email': 'contact@example.org',
                    'image': badge_image,
                }

                request = factory.post('/v1/issuer/issuers',
                                       issuer_fields_with_image,
                                       format='multipart')

                force_authenticate(request,
                                   user=get_user_model().objects.get(pk=1))
                response = view(request)
                self.assertEqual(response.status_code, 201)

                badge_object = response.data.get('json')
                derived_slug = badge_object['id'].split('/')[-1]
                new_issuer = Issuer.objects.get(slug=derived_slug)

                image_width, image_height = \
                    get_image_dimensions(new_issuer.image.file)
                self.assertEqual(image_width, 400)
                self.assertEqual(image_height, 400)

    def test_create_issuer_image_300x300_stays_300x300(self):
        view = IssuerList.as_view()

        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', '300x300.png'),
            'r') as badge_image:

                issuer_fields_with_image = {
                    'name': 'Awesome Issuer',
                    'description': 'An issuer of awe-inspiring credentials',
                    'url': 'http://example.com',
                    'email': 'contact@example.org',
                    'image': badge_image,
                }

                request = factory.post('/v1/issuer/issuers',
                                       issuer_fields_with_image,
                                       format='multipart')

                force_authenticate(request,
                                   user=get_user_model().objects.get(pk=1))
                response = view(request)
                self.assertEqual(response.status_code, 201)

                badge_object = response.data.get('json')
                derived_slug = badge_object['id'].split('/')[-1]
                new_issuer = Issuer.objects.get(slug=derived_slug)

                image_width, image_height = \
                    get_image_dimensions(new_issuer.image.file)
                self.assertEqual(image_width, 300)
                self.assertEqual(image_height, 300)

    def test_private_issuer_detail_get(self):
        # GET on single badge should work if user has privileges
        # Eventually, implement PUT for updates (if permitted)
        pass

    def test_get_empty_issuer_editors_set(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/v1/issuer/issuers/test-issuer/staff')

        self.assertEqual(response.status_code, 200)

    def test_add_user_to_issuer_editors_set(self):
        """ Authenticated user (pk=1) owns test-issuer. Add user (username=test3) as an editor. """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'username': 'test3', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(len(post_response.data), 2)  # Assert that there is now one editor

    def test_add_user_to_issuer_editors_set_by_email(self):
        """ Authenticated user (pk=1) owns test-issuer. Add user (username=test3) as an editor. """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        user_to_update = get_user_model().objects.get(email='test3@example.com')
        user_issuers = user_to_update.cached_issuers()

        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'email': 'test3@example.com', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(len(post_response.data), 2)  # Assert that there is now one editor
        self.assertTrue(len(user_issuers) < len(user_to_update.cached_issuers()))

    def test_add_user_to_issuer_editors_set_too_many_methods(self):
        """ Authenticated user (pk=1) owns test-issuer. Add user (username=test3) as an editor. """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'email': 'test3@example.com', 'username': 'test3', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 400)

    def test_add_user_to_issuer_editors_set_missing_identifier(self):
        """ Authenticated user (pk=1) owns test-issuer. Add user (username=test3) as an editor. """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 404)
        self.assertEqual(post_response.data, 'User not found. Neither email address or username was provided.')


    def test_bad_action_issuer_editors_set(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'DO THE HOKEY POKEY', 'username': 'test2', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 400)

    def test_add_nonexistent_user_to_issuer_editors_set(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'username': 'taylor_swift', 'editor': True}
        )

        self.assertContains(response, "User taylor_swift not found.", status_code=404)

    def test_add_user_to_nonexistent_issuer_editors_set(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.post(
            '/v1/issuer/issuers/test-nonexistent-issuer/staff',
            {'action': 'add', 'username': 'test2', 'editor': True}
        )

        self.assertContains(response, "Issuer test-nonexistent-issuer not found", status_code=404)

    def test_add_remove_user_with_issuer_staff_set(self):
        test_issuer = Issuer.objects.get(slug='test-issuer')
        self.assertEqual(len(test_issuer.staff.all()), 1)

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'username': 'test2'}
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(len(test_issuer.staff.all()), 2)

        second_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'remove', 'username': 'test2'}
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(len(test_issuer.staff.all()), 1)

    def test_delete_issuer_successfully(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        test_issuer = Issuer(name='issuer who can be deleted', slug='issuer-deletable')
        test_issuer.save()
        IssuerStaff(issuer=test_issuer, user=user, role=IssuerStaff.ROLE_OWNER).save()

        response = self.client.delete('/v1/issuer/issuers/issuer-deletable', {})
        self.assertEqual(response.status_code, 200)

    def test_delete_issuer_with_unissued_badgeclass_successfully(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        test_issuer = Issuer(name='issuer who can be deleted', slug="issuer-deletable")
        test_issuer.save()
        IssuerStaff(issuer=test_issuer, user=user, role=IssuerStaff.ROLE_OWNER).save()
        test_badgeclass = BadgeClass(name="Deletable Badge", issuer=test_issuer)
        test_badgeclass.save()

        response = self.client.delete('/v1/issuer/issuers/issuer-deletable', {})
        self.assertEqual(response.status_code, 200)

    def test_cant_delete_issuer_with_issued_badge(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        response = self.client.delete('/v1/issuer/issuers/test-issuer-2', {})
        self.assertEqual(response.status_code, 400)

    def test_new_issuer_updates_cached_user_issuers(self):

        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        badgelist = self.client.get('/v1/issuer/all-badges')

        example_issuer_props = {
            'name': 'Fresh Issuer',
            'description': "Fresh Issuer",
            'url': 'http://freshissuer.com',
            'email': 'prince@freshissuer.com',
        }

        response = self.client.post(
            '/v1/issuer/issuers',
            example_issuer_props
        )
        self.assertEqual(response.status_code, 201)

        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Freshness',
                'description': "Fresh Badge",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Freshness',
            }

            response = self.client.post(
                '/v1/issuer/issuers/fresh-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

        new_badgelist = self.client.get('/v1/issuer/all-badges')

        self.assertEqual(len(new_badgelist.data), len(badgelist.data) + 1)

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
class BadgeClassTests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

    def setUp(self):
        cache.clear()

    def test_create_badgeclass_for_issuer_authenticated(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

            # assert that the BadgeClass was published to and fetched from the cache
            with self.assertNumQueries(0):
                slug = response.data.get('slug')
                response = self.client.get('/v1/issuer/issuers/test-issuer/badges/{}'.format(slug))
                self.assertEqual(response.status_code, 200)

    def test_create_badgeclass_with_svg(self):
        with open(
                os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', 'test_badgeclass.svg'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

            # assert that the BadgeClass was published to and fetched from the cache
            with self.assertNumQueries(0):
                slug = response.data.get('slug')
                response = self.client.get('/v1/issuer/issuers/test-issuer/badges/{}'.format(slug))
                self.assertEqual(response.status_code, 200)

    def test_create_criteriatext_badgeclass_for_issuer_authenticated(self):
        """
        Ensure that when criteria text is submitted instead of a URL, the criteria address
        embedded in the badge is to the view that will display that criteria text
        (rather than the text itself or something...)
        """
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)
            self.assertRegexpMatches(response.data.get(
                'json', {}).get('criteria'),
                r'badge-of-awesome/criteria$'
            )

    def test_create_criteriatext_badgeclass_description_required(self):
        """
        Ensure that the API properly rejects badgeclass creation requests that do not include a description.
        """
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Awesome',
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 400)

    def test_create_badgeclass_for_issuer_unauthenticated(self):
        response = self.client.post('/v1/issuer/issuers/test-issuer/badges', {})
        self.assertEqual(response.status_code, 401)

    def test_badgeclass_list_authenticated(self):
        """
        Ensure that a logged-in user can get a list of their BadgeClasses
        """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges')

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)  # Ensure we receive a list of badgeclasses
        self.assertEqual(len(response.data), 3)  # Ensure that we receive the 3 badgeclasses in fixture as expected

    def test_unauthenticated_cant_get_badgeclass_list(self):
        """
        Ensure that logged-out user can't GET the private API endpoint for badgeclass list
        """
        response = self.client.get('/v1/issuer/issuers/test-issuer-2/badges')
        self.assertEqual(response.status_code, 401)

    def test_delete_unissued_badgeclass(self):
        self.assertTrue(BadgeClass.objects.filter(slug='badge-of-never-issued').exists())
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete('/v1/issuer/issuers/test-issuer/badges/badge-of-never-issued')
        self.assertEqual(response.status_code, 200)

        self.assertFalse(BadgeClass.objects.filter(slug='badge-of-never-issued').exists())

    def test_delete_already_issued_badgeclass(self):
        """
        A user should not be able to delete a badge class if it has been test_delete_already_issued_badgeclass
        """
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        response = self.client.delete('/v1/issuer/issuers/test-issuer/badges/badge-of-testing')
        self.assertEqual(response.status_code, 400)

        self.assertTrue(BadgeClass.objects.filter(slug='badge-of-testing').exists())

    def test_create_badgeclass_with_underscore_slug(self):
        """
        Tests that a manually-defined slug that includes underscores does not
        trigger an error when defining a new BadgeClass
        """
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Slugs',
                'slug': 'badge_of_slugs_99',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': badge_image,
                'criteria': 'The earner of this badge must slither through a garden and return home before morning.',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)
            self.assertRegexpMatches(response.data.get(
                'json', {}).get('criteria'),
                r'badge_of_slugs_99/criteria$'
            )

    def test_create_badgeclass_with_svg_image(self):
        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'test_badgeclass.svg'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

    def test_new_badgeclass_updates_cached_issuer(self):
        user = get_user_model().objects.get(pk=1)
        number_of_badgeclasses = len(list(user.cached_badgeclasses()))

        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Freshness',
                'description': "Fresh Badge",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Freshness',
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(list(user.cached_badgeclasses())), number_of_badgeclasses + 1)


    def test_new_badgeclass_updates_cached_user_badgeclasses(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        badgelist = self.client.get('/v1/issuer/all-badges')

        with open(
            os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            example_badgeclass_props = {
                'name': 'Badge of Freshness',
                'description': "Fresh Badge",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Freshness',
            }

            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

        new_badgelist = self.client.get('/v1/issuer/all-badges')

        self.assertEqual(len(new_badgelist.data), len(badgelist.data) + 1)


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
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

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

        serializer = BadgeInstanceSerializer(data=data)
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
class PublicAPITests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    def setUp(self):
        cache.clear()
        # ensure records are published to cache
        issuer = Issuer.cached.get(slug='test-issuer')
        issuer.cached_badgeclasses()
        Issuer.cached.get(pk=2)
        BadgeClass.cached.get(slug='badge-of-testing')
        BadgeClass.cached.get(pk=1)
        BadgeInstance.cached.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        pass

    def test_get_issuer_object(self):
        with self.assertNumQueries(0):
            response = self.client.get('/public/issuers/test-issuer')
            self.assertEqual(response.status_code, 200)

    def test_get_issuer_object_that_doesnt_exist(self):
        with self.assertNumQueries(1):
            response = self.client.get('/public/issuers/imaginary-issuer')
            self.assertEqual(response.status_code, 404)

    def test_get_badgeclass_image_with_redirect(self):
        with self.assertNumQueries(0):
            response = self.client.get('/public/badges/badge-of-testing/image')
            self.assertEqual(response.status_code, 302)

    def test_get_assertion_image_with_redirect(self):
        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa/image', follow=False)
            self.assertEqual(response.status_code, 302)

    def test_get_assertion_json_explicit(self):
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()
        
        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa',
                                       **{'HTTP_ACCEPT': 'application/json'})
            self.assertEqual(response.status_code, 200)

            # Will raise error if response is not JSON.
            content = json.loads(response.content)

            self.assertEqual(content['type'], 'Assertion')

    def test_get_assertion_json_implicit(self):
        """ Make sure we serve JSON by default if there is a missing Accept header. """

        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa')
            self.assertEqual(response.status_code, 200)

            # Will raise error if response is not JSON.
            content = json.loads(response.content)

            self.assertEqual(content['type'], 'Assertion')

    def test_get_assertion_html(self):
        """ Ensure hosted Assertion page returns HTML if */* is requested and that it has OpenGraph metadata properties. """
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa', **{'HTTP_ACCEPT': '*/*'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')

    def test_get_assertion_html_linkedin(self):
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa',
                                       **{'HTTP_USER_AGENT': 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')


class FindBadgeClassTests(APITestCase):
    fixtures = fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json', 'initial_my_badges']


    def test_can_find_imported_badge_by_id(self):
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        url = reverse('find_badgeclass_by_id', kwargs={'badge_id': 'http://badger.openbadges.org/badge/meta/mozfest-reveler'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), 'MozFest Reveler')

    def test_can_find_issuer_badge_by_id(self):
        # TODO: BadgeClass.identifier is mis-populated in current DB. Watch out!
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        badge = BadgeClass.objects.get(id=1)

        url = reverse('find_badgeclass_by_id', kwargs={'badge_id': badge.get_full_url()})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), 'Badge of Testing')

    def test_can_find_issuer_badge_by_slug(self):
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        url = reverse('find_badgeclass_by_slug', kwargs={'slug': 'badge-of-testing'})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), 'Badge of Awesome')