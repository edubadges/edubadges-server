from itertools import chain
from collections import OrderedDict
from PIL import Image
from rest_framework import serializers

from mainsite.utils import generate_image_url


def _decompression_bomb_check(image, max_pixels=Image.MAX_IMAGE_PIXELS):
    pixels = image.size[0] * image.size[1]
    return pixels > max_pixels


class ImageUrlGetterMixin(object):
    """
    Model mixin to get image url
    """
    def image_url(self):
        return generate_image_url(self.image)


class DefaultLanguageMixin(object):
    """
    Model mixin to get default language
    """
    @property
    def default_language(self):
        return self.institution.default_language


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
