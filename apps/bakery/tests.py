import json
import os
import os.path

from django.test import TestCase

import png_bakery
import utils

test_assertion = {
    "uid": "123",
    "issuedOn": "2015-04-01",
    "badge": "http://example.org/badge1",
    "recipient": {
        "identity": "test@example.com",
        "hashed": False
    },
    "verify": {
        "type": "hosted",
        "url": "http://example.org/badgeinstance1"
    }
}


class TypeDetectionTests(TestCase):

    def test_detect_svg_type(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'testfiles', 'baked_example.svg'
                               )) as image:
            self.assertEqual(utils.check_image_type(image), 'SVG')

    def test_detect_png_type(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'testfiles', 'public_domain_heart.png'
                               )) as image:
            self.assertEqual(utils.check_image_type(image), 'PNG')


class PNGBakingTests(TestCase):
    def test_bake_png(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'testfiles', 'public_domain_heart.png'
                               )) as image:

            return_file = png_bakery.bake(image, json.dumps(test_assertion))
            return_file.open('r')
            self.assertEqual(utils.check_image_type(return_file), 'PNG')
            return_file.close()
            return_file.open('r')
            self.assertEqual(png_bakery.unbake(return_file), json.dumps(test_assertion))

    def test_unbake_png(self):
        with open(os.path.join(os.path.dirname(__file__),
                               'testfiles', 'baked_heart.png'
                               )) as image:
            assertion = png_bakery.unbake(image)
            self.assertEqual(json.loads(assertion), test_assertion)
