# encoding: utf-8


from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

import badgrlog
from issuer.public_api import JSONComponentView
from pathway.models import PathwayElement
from pathway.renderers import PathwayElementHTMLRenderer
from pathway.serializers import PathwayElementSerializer

logger = badgrlog.BadgrLogger()


class PathwayElementJson(JSONComponentView):
    """
    GET the actual OBI badge object for a pathway element
    """
    model = PathwayElement
    renderer_classes = (JSONRenderer, PathwayElementHTMLRenderer,)
    html_renderer_class = PathwayElementHTMLRenderer

    def get(self, request, pathway_slug, element_slug, **kwargs):
        try:
            self.current_object = self.model.cached.get(slug=element_slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            self.log(self.current_object)
            serializer = PathwayElementSerializer(self.current_object)
            return Response(serializer.data)

    def get_renderer_context(self, **kwargs):
        context = super(PathwayElementJson, self).get_renderer_context(**kwargs)
        if getattr(self, 'current_object', None):
            context['pathway_element'] = self.current_object
            context['pathway'] = self.current_object.cached_pathway
            context['issuer'] = self.current_object.cached_pathway.cached_issuer
        return context

    def log(self, obj):
        logger.event(badgrlog.PathwayElementRetrievedEvent(obj, self.request))


