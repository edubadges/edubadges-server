# encoding: utf-8
from __future__ import unicode_literals

import base64
import json

from django.core.files.images import get_image_dimensions
from django.core.urlresolvers import reverse

from issuer.models import BadgeClass
from mainsite.tests import BadgrTestCase, SetupIssuerHelper
from mainsite.utils import OriginSetting


class BadgeClassTests(SetupIssuerHelper, BadgrTestCase):

    def _create_badgeclass_for_issuer_authenticated(self, image_path, **kwargs):
        with open(image_path, 'r') as badge_image:

            image_str = self._base64_data_uri_encode(badge_image, "image/png")
            example_badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': image_str,
                'criteria': 'http://wikipedia.org/Awesome',
            }
            example_badgeclass_props.update(kwargs)

            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)
            self.issuer = test_issuer
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                data=example_badgeclass_props,
                format="json"
            )
            self.assertEqual(response.status_code, 201)
            self.assertIn('slug', response.data)
            new_badgeclass_slug = response.data.get('slug')

            # assert that the BadgeClass was published to and fetched from the cache
            with self.assertNumQueries(0):
                response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badgeclass}'.format(
                    issuer=test_issuer.entity_id,
                    badgeclass=new_badgeclass_slug))
                self.assertEqual(response.status_code, 200)
                return json.loads(response.content)

    def test_can_create_badgeclass(self):
        self._create_badgeclass_for_issuer_authenticated(self.get_test_image_path())

    def test_can_create_badgeclass_with_svg(self):
        self._create_badgeclass_for_issuer_authenticated(self.get_test_svg_image_path())

    def test_create_badgeclass_scrubs_svg(self):
        with open(self.get_testfiles_path('hacked-svg-with-embedded-script-tags.svg'), 'r') as attack_badge_image:

            badgeclass_props = {
                'name': 'javascript SVG badge',
                'description': 'badge whose svg source attempts to execute code',
                'image': attack_badge_image,
                'criteria': 'http://svgs.should.not.be.user.input'
            }
            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id), badgeclass_props)
            self.assertEqual(response.status_code, 201)
            self.assertIn('slug', response.data)

            # make sure code was stripped
            bc = BadgeClass.objects.get(entity_id=response.data.get('slug'))
            image_content = bc.image.file.readlines()
            self.assertNotIn('onload', image_content)
            self.assertNotIn('<script>', image_content)

            # make sure we can issue the badge
            badgeinstance = bc.issue(recipient_id='fakerecipient@email.test')
            self.assertIsNotNone(badgeinstance)

    def test_when_creating_badgeclass_with_criteriatext_criteraurl_is_returned(self):
        """
        Ensure that when criteria text is submitted instead of a URL, the criteria address
        embedded in the badge is to the view that will display that criteria text
        (rather than the text itself or something...)
        """
        with open(self.get_test_image_path(), 'r') as badge_image:
            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id), {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            })
            self.assertEqual(response.status_code, 201)

            self.assertIn('slug', response.data)
            new_badgeclass_slug = response.data.get('slug')
            self.assertIn('json', response.data)
            self.assertIn('criteria', response.data.get('json'))
            expected_criterial_url = OriginSetting.HTTP + reverse('badgeclass_criteria', kwargs={
                'entity_id': new_badgeclass_slug
            })
            self.assertEqual(response.data.get('json').get('criteria'), expected_criterial_url)

    def test_cannot_create_badgeclass_without_description(self):
        """
        Ensure that the API properly rejects badgeclass creation requests that do not include a description.
        """
        with open(self.get_test_image_path(), 'r') as badge_image:
            badgeclass_props = {
                'name': 'Badge of Awesome',
                'image': badge_image,
                'criteria': 'The earner of this badge must be truly, truly awesome.',
            }

            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                badgeclass_props
            )
            self.assertEqual(response.status_code, 400)

    def test_cannot_create_badgeclass_if_unauthenticated(self):
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)

        response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id))
        self.assertEqual(response.status_code, 401)

    def test_can_get_badgeclass_list_if_authenticated(self):
        """
        Ensure that a logged-in user can get a list of their BadgeClasses
        """
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclasses = list(self.setup_badgeclasses(issuer=test_issuer, how_many=3))

        response = self.client.get('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.data, list)
        self.assertEqual(len(response.data), len(test_badgeclasses))

    def test_cannot_get_badgeclass_list_if_unauthenticated(self):
        """
        Ensure that logged-out user can't GET the private API endpoint for badgeclass list
        """
        test_user = self.setup_user(authenticate=False)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclasses = list(self.setup_badgeclasses(issuer=test_issuer))

        response = self.client.get('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id))
        self.assertEqual(response.status_code, 401)

    def test_can_delete_unissued_badgeclass(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        response = self.client.delete('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ))
        self.assertEqual(response.status_code, 204)

        self.assertFalse(BadgeClass.objects.filter(entity_id=test_badgeclass.entity_id).exists())

    def test_cannot_delete_already_issued_badgeclass(self):
        """
        A user should not be able to delete a badge class if it has been issued
        """
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        test_badgeclass = self.setup_badgeclass(issuer=test_issuer)

        # issue badge to a recipient
        test_badgeclass.issue(recipient_id='new.recipient@email.test')

        response = self.client.delete('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(
            issuer=test_issuer.entity_id,
            badge=test_badgeclass.entity_id
        ))
        self.assertEqual(response.status_code, 400)

        self.assertTrue(BadgeClass.objects.filter(entity_id=test_badgeclass.entity_id).exists())

    # TODO: review this test for deprecation -- we no longer allow writable slugs
    # def test_create_badgeclass_with_underscore_slug(self):
    #     """
    #     Tests that a manually-defined slug that includes underscores does not
    #     trigger an error when defining a new BadgeClass
    #     """
    #     with open(
    #             os.path.join(os.path.dirname(__file__), 'testfiles', 'guinea_pig_testing_badge.png'), 'r'
    #     ) as badge_image:
    #
    #         badgeclass_props = {
    #             'name': 'Badge of Slugs',
    #             'slug': 'badge_of_slugs_99',
    #             'description': "Recognizes slimy learners with a penchant for lettuce",
    #             'image': badge_image,
    #             'criteria': 'The earner of this badge must slither through a garden and return home before morning.',
    #         }
    #
    #         self.client.force_authenticate(user=get_user_model().objects.get(pk=1))
    #         response = self.client.post(
    #             '/v1/issuer/issuers/test-issuer/badges',
    #             badgeclass_props
    #         )
    #         self.assertEqual(response.status_code, 201)
    #         self.assertRegexpMatches(response.data.get(
    #             'json', {}).get('criteria'),
    #                                  r'badge_of_slugs_99/criteria$'
    #                                  )

    def test_cannot_create_badgeclass_with_invalid_markdown(self):
        with open(self.get_test_image_path(), 'r') as badge_image:
            badgeclass_props = {
                'name': 'Badge of Slugs',
                'slug': 'badge_of_slugs_99',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': badge_image,
            }

            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)

            # should not create badge that has images in markdown
            badgeclass_props['criteria'] = 'This is invalid ![foo](image-url) markdown'
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                badgeclass_props
            )
            self.assertEqual(response.status_code, 400)

    def test_can_create_badgeclass_with_valid_markdown(self):
        with open(self.get_test_image_path(), 'r') as badge_image:
            badgeclass_props = {
                'name': 'Badge of Slugs',
                'slug': 'badge_of_slugs_99',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': badge_image,
            }

            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)

            # valid markdown should be saved but html tags stripped
            badgeclass_props['criteria'] = 'This is *valid* markdown <p>mixed with raw</p> <script>document.write("and abusive html")</script>'
            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                badgeclass_props
            )
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.data)
            new_badgeclass = response.data
            self.assertEqual(new_badgeclass.get('criteria_text', None), 'This is *valid* markdown mixed with raw document.write("and abusive html")')
            self.assertIn('slug', new_badgeclass)

            # verify that public page renders markdown as html
            response = self.client.get('/public/badges/{}'.format(new_badgeclass.get('slug')), HTTP_ACCEPT='*/*')
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "<p>This is <em>valid</em> markdown")

    def test_can_create_badgeclass_with_alignment(self):
        with open(self.get_test_image_path(), 'r') as badge_image:
            num_badgeclasses = BadgeClass.objects.count()
            test_user = self.setup_user(authenticate=True)
            test_issuer = self.setup_issuer(owner=test_user)

            badgeclass_props = {
                'name': 'Badge of Slugs',
                'description': "Recognizes slimy learners with a penchant for lettuce",
                'image': self._base64_data_uri_encode(badge_image, 'image/png'),
                'criteriaNarrative': 'Eat lettuce. Grow big.'
            }

            # valid markdown should be saved but html tags stripped
            badgeclass_props['alignments'] = [
                {
                    'targetName': 'Align1',
                    'targetUrl': 'http://examp.e.org/frmwrk/1'
                },
                {
                    'targetName': 'Align2',
                    'targetUrl': 'http://examp.e.org/frmwrk/2'
                }
            ]
            # badgeclass_props['alignment_items'] = badgeclass_props['alignments']
            response = self.client.post(
                '/v2/issuers/{}/badgeclasses'.format(test_issuer.entity_id),
                badgeclass_props, format='json'
            )
            self.assertEqual(response.status_code, 201)
            self.assertIsNotNone(response.data)
            new_badgeclass = response.data['result'][0]
            self.assertIn('alignments', new_badgeclass.keys())
            self.assertEqual(len(new_badgeclass['alignments']), 2)
            self.assertEqual(
                new_badgeclass['alignments'][0]['targetName'], badgeclass_props['alignments'][0]['targetName'])

            # verify that public page renders markdown as html
            response = self.client.get('/public/badges/{}?v=2_0'.format(new_badgeclass.get('entityId')))
            self.assertIn('alignment', response.data.keys())
            self.assertEqual(len(response.data['alignment']), 2)
            self.assertEqual(
                response.data['alignment'][0]['targetName'], badgeclass_props['alignments'][0]['targetName'])

            self.assertEqual(num_badgeclasses + 1, BadgeClass.objects.count())

    def test_new_badgeclass_updates_cached_issuer(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        self.setup_badgeclasses(issuer=test_issuer)
        number_of_badgeclasses = len(list(test_user.cached_badgeclasses()))

        with open(self.get_test_image_path(), 'r') as badge_image:
            example_badgeclass_props = {
                'name': 'Badge of Freshness',
                'description': "Fresh Badge",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Freshness',
            }

            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                                        example_badgeclass_props)
            self.assertEqual(response.status_code, 201)

            self.assertEqual(len(list(test_user.cached_badgeclasses())), number_of_badgeclasses + 1)

    def test_new_badgeclass_updates_cached_user_badgeclasses(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)
        self.setup_badgeclasses(issuer=test_issuer)
        badgelist = self.client.get('/v1/issuer/all-badges')

        with open(self.get_test_image_path(), 'r') as badge_image:
            example_badgeclass_props = {
                'name': 'Badge of Freshness',
                'description': "Fresh Badge",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Freshness',
            }

            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                example_badgeclass_props
            )
            self.assertEqual(response.status_code, 201)

        new_badgelist = self.client.get('/v1/issuer/all-badges')

        self.assertEqual(len(new_badgelist.data), len(badgelist.data) + 1)

    def _base64_data_uri_encode(self, file, mime):
        encoded = base64.b64encode(file.read())
        return "data:{};base64,{}".format(mime, encoded)

    def test_badgeclass_put_image_data_uri(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)

        with open(self.get_test_image_path(), 'r') as badge_image:
            badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
                'criteria': 'http://wikipedia.org/Awesome',
            }

            response = self.client.post('/v1/issuer/issuers/{slug}/badges'.format(slug=test_issuer.entity_id),
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(response.status_code, 201)
            self.assertIn('slug', response.data)
            badgeclass_slug = response.data.get('slug')

        with open(self.get_testfiles_path('450x450.png'), 'r') as new_badge_image:
            put_response = self.client.put(
                '/v1/issuer/issuers/{issuer}/badges/{badge}'.format(issuer=test_issuer.entity_id, badge=badgeclass_slug),
                dict(badgeclass_props, image=self._base64_data_uri_encode(new_badge_image, 'image/png'))
            )
            self.assertEqual(put_response.status_code, 200)

            new_badgeclass = BadgeClass.objects.get(entity_id=badgeclass_slug)
            image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

            # File should be changed to new 450x450 image
            self.assertEqual(image_width, 450)
            self.assertEqual(image_height, 450)

    def test_badgeclass_put_image_non_data_uri(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)

        badgeclass_props = {
            'name': 'Badge of Awesome',
            'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
            'criteria': 'http://wikipedia.org/Awesome',
        }

        with open(self.get_testfiles_path('300x300.png'), 'r') as badge_image:
            post_response = self.client.post('/v1/issuer/issuers/{issuer}/badges'.format(issuer=test_issuer.entity_id),
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(post_response.status_code, 201)
            slug = post_response.data.get('slug')

        put_response = self.client.put('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(issuer=test_issuer.entity_id, badge=slug),
            dict(badgeclass_props, image='http://example.com/example.png')
        )
        self.assertEqual(put_response.status_code, 200)

        new_badgeclass = BadgeClass.objects.get(entity_id=slug)
        image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

        # File should be original 300x300 image
        self.assertEqual(image_width, 300)
        self.assertEqual(image_height, 300)

    def test_badgeclass_put_image_multipart(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)

        badgeclass_props = {
            'name': 'Badge of Awesome',
            'description': 'An awesome badge only awarded to awesome people or non-existent test entities',
            'criteria': 'http://wikipedia.org/Awesome',
        }

        with open(self.get_testfiles_path('300x300.png'), 'r') as badge_image:
            post_response = self.client.post('/v1/issuer/issuers/{issuer}/badges'.format(issuer=test_issuer.entity_id),
                dict(badgeclass_props, image=badge_image),
            )
            self.assertEqual(post_response.status_code, 201)
            slug = post_response.data.get('slug')

        with open(self.get_testfiles_path('450x450.png'), 'r') as new_badge_image:
            put_response = self.client.put('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(issuer=test_issuer.entity_id, badge=slug),
                dict(badgeclass_props, image=new_badge_image),
                format='multipart'
            )
            self.assertEqual(put_response.status_code, 200)

            new_badgeclass = BadgeClass.objects.get(entity_id=slug)
            image_width, image_height = get_image_dimensions(new_badgeclass.image.file)

            # File should be changed to new 450x450 image
            self.assertEqual(image_width, 450)
            self.assertEqual(image_height, 450)

    def test_badgeclass_post_get_put_roundtrip(self):
        test_user = self.setup_user(authenticate=True)
        test_issuer = self.setup_issuer(owner=test_user)

        with open(self.get_test_image_path(), 'r') as badge_image:
            example_badgeclass_props = {
                'name': 'Badge of Awesome',
                'description': "An awesome badge only awarded to awesome people or non-existent test entities",
                'image': badge_image,
                'criteria': 'http://wikipedia.org/Awesome',
            }

            post_response = self.client.post('/v1/issuer/issuers/{issuer}/badges'.format(issuer=test_issuer.entity_id),
                example_badgeclass_props,
                format='multipart'
            )
        self.assertEqual(post_response.status_code, 201)

        self.assertIn('slug', post_response.data)
        slug = post_response.data.get('slug')
        get_response = self.client.get('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(issuer=test_issuer.entity_id, badge=slug))
        self.assertEqual(get_response.status_code, 200)

        put_response = self.client.put('/v1/issuer/issuers/{issuer}/badges/{badge}'.format(issuer=test_issuer.entity_id, badge=slug),
                                       get_response.data, format='json')
        self.assertEqual(put_response.status_code, 200)

        self.assertEqual(get_response.data, put_response.data)

    def test_can_create_and_update_badgeclass_with_alignments(self):
        # create a badgeclass with alignments
        alignments = [
            {
                'target_name': "Alignment the first",
                'target_url': "http://align.ment/1",
                'target_framework': None,
                'target_code': None,
                'target_description': None,
            },
            {
                'target_name': "Second Alignment",
                'target_url': "http://align.ment/2",
                'target_framework': None,
                'target_code': None,
                'target_description': None,
            },
            {
                'target_name': "Third Alignment",
                'target_url': "http://align.ment/3",
                'target_framework': None,
                'target_code': None,
                'target_description': None,
            },
        ]
        new_badgeclass = self._create_badgeclass_for_issuer_authenticated(self.get_test_image_path(), alignment=alignments)
        self.assertEqual(alignments, new_badgeclass.get('alignment', None))

        new_badgeclass_url = '/v1/issuer/issuers/{slug}/badges/{badgeclass}'.format(
            slug=self.issuer.entity_id,
            badgeclass=new_badgeclass['slug'])

        # update alignments -- addition and deletion
        reordered_alignments = [
            alignments[0],
            alignments[1],
            {
                'target_name': "added alignment",
                'target_url': "http://align.ment/4",
                'target_framework': None,
                'target_code': None,
                'target_description': None,
            }
        ]
        new_badgeclass['alignment'] = reordered_alignments

        response = self.client.put(new_badgeclass_url, new_badgeclass, format="json")
        updated_badgeclass = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_badgeclass.get('alignment', None), reordered_alignments)

        # make sure response we got from PUT matches what we get from GET
        response = self.client.get(new_badgeclass_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, updated_badgeclass)

    def test_can_create_and_update_badgeclass_with_tags(self):
        # create a badgeclass with tags
        tags = ["first", "second", "third"]
        new_badgeclass = self._create_badgeclass_for_issuer_authenticated(self.get_test_image_path(), tags=tags)
        self.assertEqual(tags, new_badgeclass.get('tags', None))

        new_badgeclass_url = '/v1/issuer/issuers/{slug}/badges/{badgeclass}'.format(
            slug=self.issuer.entity_id,
            badgeclass=new_badgeclass['slug'])

        # update tags -- addition and deletion
        reordered_tags = ["second", "third", "fourth"]
        new_badgeclass['tags'] = reordered_tags

        response = self.client.put(new_badgeclass_url, new_badgeclass, format="json")
        updated_badgeclass = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(updated_badgeclass.get('tags', None), reordered_tags)

        # make sure response we got from PUT matches what we get from GET
        response = self.client.get(new_badgeclass_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, updated_badgeclass)

