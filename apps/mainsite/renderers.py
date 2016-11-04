from django.utils.encoding import smart_unicode
from rest_framework import renderers


class JSONLDRenderer(renderers.JSONRenderer):
    """
    A simple wrapper for JSONRenderer that declares that we're delivering LD.
    """
    media_type = 'application/ld+json'
    format = 'ld+json'


class CSVRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        return data.encode(self.charset)
