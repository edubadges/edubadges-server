import io

from backports import csv
from rest_framework import renderers


class JSONLDRenderer(renderers.JSONRenderer):
    """
    A simple wrapper for JSONRenderer that declares that we're delivering LD.
    """
    media_type = 'application/ld+json'
    format = 'ld+json'


class CSVDictRenderer(renderers.BaseRenderer):
    media_type = 'text/csv'
    format = 'csv'

    def render(self, data, media_type=None, renderer_context=None):
        response = renderer_context.get('response', None)

        if response is not None and response.exception:
            return None
        else:
            fieldnames = data['fieldnames']
            rows = data['rowdicts']

        buff = io.StringIO()
        writer = csv.DictWriter(buff, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        return buff.getvalue().encode(self.charset)
