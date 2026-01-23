#!/usr/bin/env python

from django.test import SimpleTestCase


class BasicMobileAPITest(SimpleTestCase):
    def test_simple_math(self):
        """A very basic test that doesn't import any models"""
        self.assertEqual(2 + 2, 4)

    def test_string_operations(self):
        """Another basic test"""
        self.assertEqual('hello'.upper(), 'HELLO')
