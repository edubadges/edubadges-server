import io

from itertools import chain
from collections import OrderedDict
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image
from resizeimage.resizeimage import resize_contain
from rest_framework import serializers
from xml.etree import cElementTree as ET

from mainsite.utils import verify_svg, generate_image_url


def _decompression_bomb_check(image, max_pixels=Image.MAX_IMAGE_PIXELS):
    pixels = image.size[0] * image.size[1]
    return pixels > max_pixels


class ImageUrlGetterMixin(object):
    """
    Model mixin to get image url
    """
    def image_url(self):
        return generate_image_url(self.image)


# class ResizeUploadedImage(object):
#
#     def save(self, *args, **kwargs):
#         if self.pk is None and self.image:
#             try:
#                 f = open(self.image.name, 'rb')
#                 image = Image.open(f)
#                 if _decompression_bomb_check(image):
#                     raise ValidationError("Invalid image")
#             except IOError:
#                 return super(ResizeUploadedImage, self).save(*args, **kwargs)
#
#             if image.format == 'PNG':
#                 max_square = getattr(settings, 'IMAGE_FIELD_MAX_PX', 400)
#
#                 smaller_than_canvas = \
#                     (image.width < max_square and image.height < max_square)
#
#                 if smaller_than_canvas:
#                     max_square = (image.width
#                                   if image.width > image.height
#                                   else image.height)
#
#                 new_image = resize_contain(image, (max_square, max_square))
#
#                 byte_string = io.BytesIO()
#                 new_image.save(byte_string, 'PNG')
#
#                 self.image = InMemoryUploadedFile(byte_string, None,
#                                                   self.image.name, 'image/png',
#                                                   byte_string.getvalue().__len__(), None)
#
#         return super(ResizeUploadedImage, self).save(*args, **kwargs)
#
#
# class ScrubUploadedSvgImage(object):
#     MALICIOUS_SVG_TAGS = [
#         "script"
#     ]
#     MALICIOUS_SVG_ATTRIBUTES = [
#         "onload"
#     ]
#     SVG_NAMESPACE = "http://www.w3.org/2000/svg"
#
#     def save(self, *args, **kwargs):
#         if self.pk is None and self.image and verify_svg(self.image.file):
#             self.image.file.seek(0)
#             ET.register_namespace("", self.SVG_NAMESPACE)
#             tree = ET.parse(self.image.file)
#             root = tree.getroot()
#
#             # strip malicious tags
#             elements_to_strip = []
#             for tag_name in self.MALICIOUS_SVG_TAGS:
#                 elements_to_strip.extend( root.findall('{{{ns}}}{tag}'.format(ns=self.SVG_NAMESPACE, tag=tag_name)) )
#             for e in elements_to_strip:
#                 root.remove(e)
#
#             # strip malicious attributes
#             for el in tree.iter():
#                 for attrib_name in self.MALICIOUS_SVG_ATTRIBUTES:
#                     if attrib_name in el.attrib:
#                         del el.attrib[attrib_name]
#
#             # write out scrubbed svg
#             buf = io.BytesIO()
#             tree.write(buf)
#             self.image = InMemoryUploadedFile(buf, 'image', self.image.name, 'image/svg+xml', buf.len, 'utf8')
#         return super(ScrubUploadedSvgImage, self).save(*args, **kwargs)


class InternalValueErrorOverrideMixin(object):
    """
    Mixin used to override errors created when to_internal_value() Serializer method is called
    create your own to_internal_value_error_override() method to go along with this mixin.
    """
    def to_internal_value(self, data):
        errors = self.to_internal_value_error_override(data)
        if errors:
            try:
                super(InternalValueErrorOverrideMixin, self).to_internal_value(data)
                raise serializers.ValidationError(detail=errors)
            except serializers.ValidationError as e:
                e.detail = OrderedDict(chain(e.detail.items(), errors.items()))
                raise e
        else:
            return super(InternalValueErrorOverrideMixin, self).to_internal_value(data)