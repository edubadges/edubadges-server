# encoding: utf-8
from __future__ import unicode_literals

import base64
import os.path

import os
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.images import get_image_dimensions
from django.test import override_settings
from mainsite import TOP_DIR
from rest_framework.test import APITestCase

from issuer.models import BadgeClass


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
    # fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']

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
            # we expect to generate one query where the object permissions are checked in BadgeClassDetail.get
            with self.assertNumQueries(1):
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
            # we expect to generate one query where the object permissions are checked in BadgeClassDetail.get
            with self.assertNumQueries(1):
                slug = response.data.get('slug')
                response = self.client.get('/v1/issuer/issuers/test-issuer/badges/{}'.format(slug))
                self.assertEqual(response.status_code, 200)

    def test_create_badgeclass_scrubs_svg(self):
        with open(
                os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', 'hacked-svg-with-embedded-script-tags.svg'), 'r'
        ) as attack_badge_image:

            badgeclass_props = {
                'name': 'javascript SVG badge',
                'description': 'badge whose svg source attempts to execute code',
                'image': attack_badge_image,
                'criteria': 'http://svgs.should.not.be.user.input'
            }
            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
            response = self.client.post('/v1/issuer/issuers/test-issuer/badges', badgeclass_props)
            self.assertEqual(response.status_code, 201)

            # make sure code was stripped
            bc = BadgeClass.objects.get(slug=response.data.get('slug'))
            image_content = bc.image.file.readlines()
            self.assertNotIn('onload', image_content)
            self.assertNotIn('<script>', image_content)

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

    def test_dont_create_badgeclass_with_invalid_markdown(self):
        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Slugs',
                'slug': 'badge_of_slugs_99',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': badge_image,
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

            # should not create badge that has images in markdown
            badgeclass_props['criteria'] = 'This is invalid ![foo](image-url) markdown'
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 400)

    def test_create_badgeclass_with_valid_markdown(self):
        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
        ) as badge_image:

            badgeclass_props = {
                'name': 'Badge of Slugs',
                'slug': 'badge_of_slugs_99',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': badge_image,
            }

            self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

            # valid markdown should be saved but html tags stripped
            badgeclass_props['criteria'] = 'This is *valid* markdown <p>mixed with raw</p> <script>document.write("and abusive html")</script>'
            response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.data)
            new_badgeclass = response.data
            self.assertEqual(new_badgeclass.get('criteria_text', None), 'This is *valid* markdown mixed with raw document.write("and abusive html")')

            # verify that public page renders markdown as html
            response = self.client.get('/public/badges/{}'.format(new_badgeclass.get('slug')), HTTP_ACCEPT='*/*')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "<p>This is <em>valid</em> markdown")

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

    def _base64_data_uri_encode(self, file, mime):
        encoded = base64.b64encode(file.read())
        return "data:{};base64,{}".format(mime, encoded)

    def test_badgeclass_put_image_data_uri(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        badgeclass_props = {
            'name': 'Badge of Awesome',
            'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
            'criteria': 'http://wikipedia.org/Awesome',
        }

        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', '300x300.png'), 'r'
        ) as badge_image:
            post_response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(post_response.status_code, 201)
            slug = post_response.data.get('slug')

        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', '450x450.png'), 'r'
        ) as new_badge_image:
            put_response = self.client.put(
                '/v1/issuer/issuers/test-issuer/badges/{}'.format(slug),
                dict(badgeclass_props, image=self._base64_data_uri_encode(new_badge_image, 'image/png'))
            )
            self.assertEqual(put_response.status_code, 200)

            new_badgeclass = BadgeClass.objects.get(slug=slug)
            image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

            # File should be changed to new 450x450 image
            self.assertEqual(image_width, 450)
            self.assertEqual(image_height, 450)

    def test_badgeclass_put_image_non_data_uri(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        badgeclass_props = {
            'name': 'Badge of Awesome',
            'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
            'criteria': 'http://wikipedia.org/Awesome',
        }

        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', '300x300.png'), 'r'
        ) as badge_image:
            post_response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(post_response.status_code, 201)
            slug = post_response.data.get('slug')

        put_response = self.client.put(
            '/v1/issuer/issuers/test-issuer/badges/{}'.format(slug),
            dict(badgeclass_props, image='http://example.com/example.png')
        )
        self.assertEqual(put_response.status_code, 200)

        new_badgeclass = BadgeClass.objects.get(slug=slug)
        image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

        # File should be original 300x300 image
        self.assertEqual(image_width, 300)
        self.assertEqual(image_height, 300)

    def test_badgeclass_put_image_multipart(self):
        self.client.force_authenticate(user=get_user_model().objects.get(pk=1))

        badgeclass_props = {
            'name': 'Badge of Awesome',
            'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
            'criteria': 'http://wikipedia.org/Awesome',
        }

        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', '300x300.png'), 'r'
        ) as badge_image:
            post_response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(post_response.status_code, 201)
            slug = post_response.data.get('slug')

        with open(
                os.path.join(os.path.dirname(__file__), 'testfiles', '450x450.png'), 'r'
        ) as new_badge_image:
            put_response = self.client.put(
                '/v1/issuer/issuers/test-issuer/badges/{}'.format(slug),
                dict(badgeclass_props, image=new_badge_image),
                format='multipart'
            )
            self.assertEqual(put_response.status_code, 200)

            new_badgeclass = BadgeClass.objects.get(slug=slug)
            image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

            # File should be changed to new 450x450 image
            self.assertEqual(image_width, 450)
            self.assertEqual(image_height, 450)


    def test_badgeclass_post_get_put_roundtrip(self):
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
            post_response = self.client.post(
                '/v1/issuer/issuers/test-issuer/badges',
                example_badgeclass_props,
                format='multipart'
            )
        self.assertEqual(post_response.status_code, 201)

        slug = post_response.data.get('slug')
        get_response = self.client.get('/v1/issuer/issuers/test-issuer/badges/{}'.format(slug))
        self.assertEqual(get_response.status_code, 200)

        put_response = self.client.put('/v1/issuer/issuers/test-issuer/badges/{}'.format(slug), get_response.data)
        self.assertEqual(put_response.status_code, 200)

        self.assertEqual(get_response.data, put_response.data)



