# encoding: utf-8
from __future__ import unicode_literals

from rest_framework.renderers import BrowsableAPIRenderer


class PathwayElementHTMLRenderer(BrowsableAPIRenderer):
    media_type = 'text/html'
    template = 'public/pathway_element.html'

    def get_context(self, data, accepted_media_type, renderer_context):
        context = super(PathwayElementHTMLRenderer, self).get_context(
            data, accepted_media_type, renderer_context)

        context['issuer'] = renderer_context.get('issuer')
        context['pathway'] = renderer_context.get('pathway')
        context['pathway_element'] = renderer_context.get('pathway_element')

        return context



