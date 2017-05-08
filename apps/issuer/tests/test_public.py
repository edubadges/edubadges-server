# encoding: utf-8
from __future__ import unicode_literals

import json

import os
from django.core.cache import cache
from django.test import override_settings
from mainsite import TOP_DIR
from rest_framework.test import APITestCase

from issuer.models import Issuer, BadgeClass, BadgeInstance


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
    # fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json']
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
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()
        assertion.cached_evidence()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa/image', follow=False)
            self.assertEqual(response.status_code, 302)

    def test_get_assertion_json_explicit(self):
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()
        assertion.cached_evidence()

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
        assertion.cached_evidence()

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
        assertion.cached_evidence()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa', **{'HTTP_ACCEPT': '*/*'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')

    def test_get_assertion_html_linkedin(self):
        assertion = BadgeInstance.objects.get(slug='92219015-18a6-4538-8b6d-2b228e47b8aa')
        assertion.issuer.cached_badgeclasses()
        assertion.cached_evidence()

        with self.assertNumQueries(0):
            response = self.client.get('/public/assertions/92219015-18a6-4538-8b6d-2b228e47b8aa',
                                       **{'HTTP_USER_AGENT': 'LinkedInBot/1.0 (compatible; Mozilla/5.0; Jakarta Commons-HttpClient/3.1 +http://www.linkedin.com)'})
            self.assertEqual(response.status_code, 200)

            self.assertContains(response, '<meta property="og:url"')




