from backports import csv
import StringIO

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

            # TODO: Replace return None with commented lines below to get human-readable description in response
            #
            # Returning a non-None value in this function, as part of the exception handling code path in Django REST
            # Framework, generates an HTTP response that Chrome rejects as invalid (ERR_INVALID_RESPONSE).  Possible
            # Django REST Framework bug?
            #
            # fieldnames = data.keys()
            # rows = [data]
        else:
            fieldnames = data['fieldnames']
            rows = data['rowdicts']

        buff = StringIO.StringIO()
        writer = csv.DictWriter(buff, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        return buff.getvalue().encode(self.charset)
