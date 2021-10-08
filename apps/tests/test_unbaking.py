import hashlib
import json
import os
import unittest

from openbadges_bakery import unbake


class TestBaking(unittest.TestCase):

    def test_unbake_svg(self):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, 'files', 'baked_svg_edubadge.svg'), 'rb') as image:
            verify_url = unbake(image)
            self.assertEqual('http://localhost:8000/public/assertions/0SiqaDWfS3CXi2gCg72j_A', verify_url.decode())

    def test_unbake_png(self):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, 'files', 'introduction_to_political_science_edubadge.png'), 'rb') as image:
            assertion = unbake(image)
            data = json.loads(assertion)
            self.assertEqual('http://localhost:8000/public/assertions/DeUa447WR4mScC-4DgJomw', data['id'])

    def test_unbake_png_file_type(self):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, 'files', 'Test Issuer - Software Developer - 2021-10-08.png'), 'rb') as image:
            assertion = unbake(image)
            data = json.loads(assertion)
            self.assertEqual('https://api.eu.badgr.io/public/assertions/icXbWEu3QSearLfeO1MEwA', data['id'])

    def test_unbake_eu_badgr_png(self):
        dirname = os.path.dirname(__file__)
        with open(os.path.join(dirname, 'files', 'test_badge_interoperability.png'), 'rb') as image:
            assertion = unbake(image)
            data = json.loads(assertion)
            self.assertEqual('https://api.eu.badgr.io/public/assertions/10Ou1MgvRRCEXvZufypxeA', data['id'])

            recipient = data['recipient']
            salt = recipient['salt']
            value = 'sha256$' + hashlib.sha256('oharsta@zilverline.com'.encode() + salt.encode()).hexdigest()
            self.assertEqual(value, recipient['identity'])
