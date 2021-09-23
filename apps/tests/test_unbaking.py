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
            verify_url = unbake(image)
            self.assertEqual('http://localhost:8000/public/assertions/0SiqaDWfS3CXi2gCg72j_A', verify_url)
