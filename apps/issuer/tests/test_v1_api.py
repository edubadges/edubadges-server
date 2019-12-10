# encoding: utf-8

from django.urls import reverse
from mainsite.tests import SetupIssuerHelper, BadgrTestCase


class FindBadgeClassTests(SetupIssuerHelper, BadgrTestCase):

    #@unittest.skip('For debug speedup')
    def test_can_find_imported_badge_by_id(self):
        user = self.setup_user(authenticate=True)
        issuer = self.setup_issuer(owner=user)
        badgeclass = self.setup_badgeclass(issuer=issuer)

        source_url = 'https://imported.fake/badge/url'
        badgeclass.source_url = source_url
        badgeclass.save()

        url = "{url}?identifier={id}".format(
            url=reverse('v1_api_find_badgeclass_by_identifier'),
            id=source_url
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('slug', response.data)
        self.assertEqual(response.data['slug'], badgeclass.entity_id)

    #@unittest.skip('For debug speedup')
    def test_can_find_issuer_badge_by_id(self):
        user = self.setup_user(authenticate=True)
        issuer = self.setup_issuer(owner=user)
        badgeclass = self.setup_badgeclass(issuer=issuer)

        url = "{url}?identifier={id}".format(
            url=reverse('v1_api_find_badgeclass_by_identifier'),
            id=badgeclass.jsonld_id
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('slug', response.data)
        self.assertEqual(response.data['slug'], badgeclass.entity_id)

    #@unittest.skip('For debug speedup')
    def test_can_find_issuer_badge_by_slug(self):
        user = self.setup_user(authenticate=True)
        issuer = self.setup_issuer(owner=user)
        badgeclass = self.setup_badgeclass(issuer=issuer)
        badgeclass.slug = 'legacy-slug'
        badgeclass.save()

        url = "{url}?identifier={slug}".format(
            url=reverse('v1_api_find_badgeclass_by_identifier'),
            slug=badgeclass.slug
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('slug', response.data)
        self.assertEqual(response.data['slug'], badgeclass.entity_id)


