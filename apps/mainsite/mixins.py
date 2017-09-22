import StringIO
import math
from xml.etree import cElementTree as ET

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from mainsite.utils import verify_svg


def resize_contain(image, size):
    """
    Resize image according to size.
    image:      a Pillow image instance
    size:       a list of two integers [width, height]

    taken from python-resize-image==1.1.10
    """
    img_format = image.format
    img = image.copy()
    img.thumbnail((size[0], size[1]), Image.LANCZOS)
    background = Image.new('RGBA', (size[0], size[1]), (255, 255, 255, 0))
    img_position = (
        int(math.ceil((size[0] - img.size[0]) / 2)),
        int(math.ceil((size[1] - img.size[1]) / 2))
    )
    background.paste(img, img_position)
    background.format = img_format
    return background


class ResizeUploadedImage(object):

    def save(self, *args, **kwargs):
        if self.pk is None and self.image:
            try:
                image = Image.open(self.image)
            except IOError:
                return super(ResizeUploadedImage, self).save(*args, **kwargs)

            if image.format == 'PNG':
                max_square = getattr(settings, 'IMAGE_FIELD_MAX_PX', 400)

                smaller_than_canvas = \
                    (image.width < max_square and image.height < max_square)

                if smaller_than_canvas:
                    max_square = (image.width
                                  if image.width > image.height
                                  else image.height)

                new_image = resize_contain(image, (max_square, max_square))

                byte_string = StringIO.StringIO()
                new_image.save(byte_string, 'PNG')

                self.image = InMemoryUploadedFile(byte_string, None,
                                                  self.image.name, 'image/png',
                                                  byte_string.len, None)

        return super(ResizeUploadedImage, self).save(*args, **kwargs)


class ScrubUploadedSvgImage(object):
    MALICIOUS_SVG_TAGS = [
        "script"
    ]
    MALICIOUS_SVG_ATTRIBUTES = [
        "onload"
    ]
    SVG_NAMESPACE = "http://www.w3.org/2000/svg"

    def save(self, *args, **kwargs):
        if self.pk is None and self.image and verify_svg(self.image.file):
            self.image.file.seek(0)
            ET.register_namespace("", self.SVG_NAMESPACE)
            tree = ET.parse(self.image.file)
            root = tree.getroot()

            # strip malicious tags
            elements_to_strip = []
            for tag_name in self.MALICIOUS_SVG_TAGS:
                elements_to_strip.extend( root.findall('{{{ns}}}{tag}'.format(ns=self.SVG_NAMESPACE, tag=tag_name)) )
            for e in elements_to_strip:
                root.remove(e)

            # strip malicious attributes
            for el in tree.iter():
                for attrib_name in self.MALICIOUS_SVG_ATTRIBUTES:
                    if attrib_name in el.attrib:
                        del el.attrib[attrib_name]

            # write out scrubbed svg
            buf = StringIO.StringIO()
            tree.write(buf)
            self.image = InMemoryUploadedFile(buf, 'image', self.image.name, 'image/svg+xml', buf.len, 'utf8')
        return super(ScrubUploadedSvgImage, self).save(*args, **kwargs)
