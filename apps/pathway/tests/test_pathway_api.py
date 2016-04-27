# Created by wiggins@concentricsky.com on 4/16/16.
import json
import os
import time

from allauth.account.models import EmailAddress
from django.core.cache import cache
from django.core.cache.backends.filebased import FileBasedCache
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from badgeuser.models import BadgeUser
from mainsite import TOP_DIR


@override_settings(
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
            'LOCATION': os.path.join(TOP_DIR, 'test.cache'),
        }
    },
)
class CachingTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        test_cache = FileBasedCache(os.path.join(TOP_DIR, 'test.cache'), {})
        test_cache.clear()

    def setUp(self):
        # scramble the cache key each time
        cache.key_prefix = "test{}".format(str(time.time()))


class PathwayApiTests(APITestCase, CachingTestCase):

    def setUp(self):
        super(PathwayApiTests, self).setUp()

        # instructor
        self.instructor = BadgeUser(username='instructor', email='instructor@local.test')
        self.instructor.set_password('secret')
        self.instructor.save()
        EmailAddress(email='instructor@local.test', verified=True, primary=True, user=self.instructor).save()
        self.assertTrue(self.client.login(username='instructor', password='secret'), "Instructor can log in")

        # issuer
        issuer_data = {
            'name': 'Unit Test Issuer',
            'description': "Issuer from unit test",
            'url': "http://example.test",
            'email': "unittest@example.test",
        }
        response = self.client.post(reverse('issuer_list'), issuer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created an issuer")
        self.assertTrue(response.data['slug'], "Received an issuer with a slug")
        self.issuer = response.data

    def test_can_create_pathway(self):
        pathway_data = {
            'name': "Test Career Pathway",
            'description': "Students pathway through the testing career",
        }
        response = self.client.post(reverse('pathway_list', kwargs={'issuer_slug': self.issuer.get('slug')}), pathway_data, format='json')
        pathway = response.data
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway")

        # Plumber
        # plumbing badges
        with open(os.path.join(TOP_DIR, 'apps', 'issuer', 'testfiles', 'guinea_pig_testing_badge.png')) as badge_image:
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Plumber",
                'description': "You plumb now",
                'criteria': "Learn what it is to be a plumber",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            plumber_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Intro Plumbing Badge",
                'description': "You learn to plumb",
                'criteria': "learn plumbing basics",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            intro_plumbing_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Advanced Plumbing 1 Badge",
                'description': "You plumb good 1",
                'criteria': "advanced plumbing method 1",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            adv1_plumbing_badge = response.data

            badge_image.seek(0)
            response = self.client.post(reverse('badgeclass_list', kwargs={'issuerSlug': self.issuer.get('slug')}), {
                'name': "Advanced Plumbing 2 Badge",
                'description': "You plumb good 2",
                'criteria': "advanced plumbing method 2",
                'image': badge_image,
            })
            self.assertEqual(response.status_code, 201)
            adv2_plumbing_badge = response.data

        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': pathway['rootElement'],
            'name': 'Plumber',
            'description': 'You can plumb things for people.',
            'completionBadge': plumber_badge['json']['id'],
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        plumber_element = response.data

        # Intro to Plumbing
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': plumber_element['@id'],
            'name': 'Intro to Plumbing',
            'description': 'You learn the basics of plumbing.',
            'requirements': json.dumps({
                '@type': 'BadgeJunction',
                'junctionConfig': {
                    '@type': 'Conjunction',
                    'requiredNumber': 1,
                },
                'badges': [
                    intro_plumbing_badge['json']['id']
                ],
            })
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        intro_plumbing_element = response.data

        # Advanced Plumbing
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
             'parent': plumber_element['@id'],
             'name': 'Advanced Plumbing',
             'description': 'You learn all about plumbing.',
             'requirements': json.dumps({
                 '@type': 'BadgeJunction',
                 'junctionConfig': {
                     '@type': 'Disjunction',
                     'requiredNumber': 1,
                 },
                 'badges': [
                     adv1_plumbing_badge['json']['id'],
                     adv2_plumbing_badge['json']['id']
                 ],
             })
         }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        adv_plumbing_element = response.data

        # update requirements
        plumber_element.update({
            'requirements': {
                '@type': 'ElementJunction',
                'junctionConfig': {
                    '@type': 'Conjunction',
                    'requiredNumber': 2,
                },
                'elements': [
                    intro_plumbing_element['@id'],
                    adv_plumbing_element['@id']
                ],
            }
        })
        response = self.client.put(reverse('pathway_element_detail', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug'),
            'element_slug': plumber_element.get('slug')
        }), plumber_element, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Updated pathway element")
        updated_plumber_element = response.data

        # Teacher
        response = self.client.post(reverse('pathway_element_list', kwargs={
            'issuer_slug': self.issuer.get('slug'),
            'pathway_slug': pathway.get('slug')
        }), {
            'parent': pathway['rootElement'],
            'name': 'Teacher',
            'description': 'You can teache people things.',
            'ordering': 1,
            'alignmentUrl': "http://unit.fake.test",
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, "Created pathway element")
        teacher_element = response.data


