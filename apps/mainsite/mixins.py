import StringIO

from PIL import Image
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from resizeimage.resizeimage import resize_contain
from xml.etree import cElementTree as ET

from mainsite.utils import verify_svg


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
    def save(self, *args, **kwargs):
        if self.pk is None and self.image and verify_svg(self.image.file):
            self.image.file.seek(0)
            tree = ET.parse(self.image.file)
            for el in tree.iter():
                if 'onload' in el.attrib:
                    del el.attrib['onload']
            buf = StringIO.StringIO()
            tree.write(buf)
            self.image = InMemoryUploadedFile(buf, 'image', self.image.name, 'image/svg+xml', buf.len, 'utf8')
        return super(ScrubUploadedSvgImage, self).save(*args, **kwargs)
