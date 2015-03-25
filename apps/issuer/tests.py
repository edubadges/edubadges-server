from django.test import TestCase, Client
from django.test.utils import override_settings


class IssuerTests(TestCase):
    pass


class PublicAPITests(TestCase):
    # fixtures = ['0001_initial_superuser.json','test_issuer_models.json','test_badge_objects.json']
    """
    Tests the ability of an anonymous user to GET one public badge object
    """
    def test_get_issuer_object(self):
        pass