import os
from unittest import TestCase
from ..settings import legacy_boolean_parsing

class TestLegacyBooleanParsing(TestCase):
    def setUp(self):
        # Store any existing environment variables to restore them later
        self.original_env = os.environ.copy()

    def tearDown(self):
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_string_true_returns_true(self):
        os.environ['TEST_KEY'] = 'True'
        self.assertTrue(legacy_boolean_parsing('TEST_KEY', '0'))

    def test_string_false_returns_false(self):
        os.environ['TEST_KEY'] = 'False'
        self.assertFalse(legacy_boolean_parsing('TEST_KEY', '1'))

    def test_numeric_1_returns_true(self):
        os.environ['TEST_KEY'] = '1'
        self.assertTrue(legacy_boolean_parsing('TEST_KEY', '0'))

    def test_numeric_0_returns_false(self):
        os.environ['TEST_KEY'] = '0'
        self.assertFalse(legacy_boolean_parsing('TEST_KEY', '1'))

    def test_missing_key_returns_default_true(self):
        self.assertTrue(legacy_boolean_parsing('NONEXISTENT_KEY', '1'))

    def test_missing_key_returns_default_false(self):
        self.assertFalse(legacy_boolean_parsing('NONEXISTENT_KEY', '0'))

    def test_invalid_value_raises_value_error(self):
        os.environ['TEST_KEY'] = 'invalid'
        with self.assertRaises(ValueError):
            legacy_boolean_parsing('TEST_KEY', '0')
