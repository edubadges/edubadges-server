# encoding: utf-8
from __future__ import unicode_literals

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from rest_framework.test import APITestCase

from issuer.models import BadgeClass


class FindBadgeClassTests(APITestCase):
    # fixtures = fixtures = ['0001_initial_superuser.json', 'test_badge_objects.json', 'initial_my_badges']

    def test_can_find_imported_badge_by_id(self):
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        url = "{url}?identifier={id}".format(
            url=reverse('find_badgeclass_by_identifier'),
            id='http://badger.openbadges.org/badge/meta/mozfest-reveler'
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), 'MozFest Reveler')

    def test_can_find_issuer_badge_by_id(self):
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        badge = BadgeClass.objects.get(id=1)

        url = "{url}?identifier={id}".format(
            url=reverse('find_badgeclass_by_identifier'),
            id=badge.jsonld_id
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), badge.name)

    def test_can_find_issuer_badge_by_slug(self):
        user = get_user_model().objects.first()
        self.client.force_authenticate(user=user)

        url = "{url}?identifier={slug}".format(
            url=reverse('find_badgeclass_by_identifier'),
            slug='fresh-badge-of-testing'
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['json'].get('name'), 'Fresh Badge of Testing')


