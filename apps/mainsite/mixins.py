import StringIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
from resizeimage.resizeimage import resize_contain


class ResizeUploadedImage(object):

    def save(self, *args, **kwargs):
        if self.pk is None and self.image:
            image = Image.open(self.image)

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
