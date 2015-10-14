import StringIO

from django.core.files.uploadedfile import InMemoryUploadedFile

from PIL import Image
from resizeimage.resizeimage import resize_contain


class ResizeUploadedImage(object):

    def save(self, *args, **kwargs):
        if self.pk is None:
            image = Image.open(self.image)

            if image.format == 'PNG':
                new_image = resize_contain(image, (400, 400))

                byte_string = StringIO.StringIO()
                new_image.save(byte_string, 'PNG')

                self.image = InMemoryUploadedFile(byte_string, None,
                                                  self.image.name, 'image/png',
                                                  byte_string.len, None)

        return super(ResizeUploadedImage, self).save(*args, **kwargs)
