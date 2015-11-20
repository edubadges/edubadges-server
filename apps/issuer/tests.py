import json
import os
import os.path
import png
import shutil

from django.core import mail
from django.core.files.images import get_image_dimensions
from django.contrib.auth import get_user_model

from openbadges_bakery import unbake
from rest_framework.test import APIRequestFactory, APITestCase, force_authenticate

from issuer.api import IssuerList
from issuer.models import Issuer, BadgeClass, BadgeInstance

factory = APIRequestFactory()

example_issuer_props = {
    'name': 'Awesome Issuer',
    'description': 'An issuer of awe-inspiring credentials',
    'url': 'http://example.com',
    'email': 'contact@example.org'
}


class IssuerTests(APITestCase):
    fixtures = ['0001_initial_superuser', 'test_badge_objects.json']

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
        view = IssuerList.as_view()

        request = factory.post(
            '/v1/issuer/issuers',
            json.dumps(example_issuer_props),
            content_type='application/json'
        )

        force_authenticate(request, user=get_user_model().objects.get(pk=1))
        response = view(request)
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

        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'email': 'test3@example.com', 'editor': True}
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(len(post_response.data), 2)  # Assert that there is now one editor

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
        self.assertEqual(len(test_issuer.staff.all()), 0)

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        post_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'add', 'username': 'test2'}
        )

        self.assertEqual(post_response.status_code, 200)
        self.assertEqual(len(test_issuer.staff.all()), 1)

        second_response = self.client.post(
            '/v1/issuer/issuers/test-issuer/staff',
            {'action': 'remove', 'username': 'test2'}
        )

        self.assertEqual(second_response.status_code, 200)
        self.assertEqual(len(test_issuer.staff.all()), 0)

    def test_delete_issuer_successfully(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        test_issuer = Issuer(name='issuer who can be deleted', slug='issuer-deletable', owner=user)
        test_issuer.save()

        response = self.client.delete('/v1/issuer/issuers/issuer-deletable', {})
        self.assertEqual(response.status_code, 200)

    def test_cant_delete_issuer_with_issued_badge(self):
        user = get_user_model().objects.get(pk=1)
        self.client.force_authenticate(user=user)
        response = self.client.delete('/v1/issuer/issuers/test-issuer-2', {})
        self.assertEqual(response.status_code, 400)


class BadgeClassTests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

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
        self.assertEqual(len(response.data), 2)  # Ensure that we receive the 3 badgeclasses in fixture as expected

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


class AssertionTests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

    def ensure_image_exists(self, badge_object):
        if not os.path.exists(badge_object.image.path):
            shutil.copy2(
                os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'),
                badge_object.image.path
            )

    def test_authenticated_owner_issue_badge(self):
        # load test image into media files if it doesn't exist
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))

        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
        assertion = {
            "email": "test@example.com"
        }
        response = self.client.post('/v1/issuer/issuers/test-issuer-2/badges/badge-of-testing/assertions', assertion)

        self.assertEqual(response.status_code, 201)

        # assert that the BadgeInstance was published to and fetched from cache
        with self.assertNumQueries(1): # 1 query allowed for Badgebook recipient obscuring
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

    def test_authenticated_editor_can_issue_badge(self):
        # load test image into media files if it doesn't exist
        self.ensure_image_exists(BadgeClass.objects.get(slug='badge-of-testing'))

        # This issuer has user 2 among its editors.
        the_editor = get_user_model().objects.get(pk=2)
        self.client.force_authenticate(user=the_editor)
        response = self.client.post(
            '/v1/issuer/issuers/edited-test-issuer/badges/badge-of-edited-testing/assertions',
            {"email": "test@example.com"}
        )

        self.assertEqual(response.status_code, 201)

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


class PublicAPITests(APITestCase):
    fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    def setUp(self):
        # ensure records are published to cache
        Issuer.cached.get(slug='test-issuer')
        BadgeClass.cached.get(slug='badge-of-testing')
        BadgeInstance.cached.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa', revoked=False)
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
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa/image')
            self.assertEqual(response.status_code, 302)
