#!/usr/bin/env python

from django.test import SimpleTestCase


class SimpleMobileAPITest(SimpleTestCase):
    def test_simple_addition(self):
        """A simple test that doesn't require database or complex setup"""
        self.assertEqual(1 + 1, 2)

    def test_api_endpoints_exist(self):
        """Test that API endpoints are defined"""
        from apps.mobile_api.api_urls import urlpatterns

        self.assertGreater(len(urlpatterns), 0)
