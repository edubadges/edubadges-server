# encoding: utf-8
from __future__ import unicode_literals

from apispec_drf.decorators import apispec_list_operation
from rest_framework.exceptions import ValidationError

from entity.api import BaseEntityListView, BaseEntityDetailView
from externaltools.models import ExternalTool, ExternalToolLaunchpoint
from externaltools.serializers_v1 import ExternalToolSerializerV1, ExternalToolLaunchSerializerV1
from externaltools.serializers_v2 import ExternalToolSerializerV2, ExternalToolLaunchSerializerV2
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class ExternalToolList(BaseEntityListView):
    model = ExternalTool
    v1_serializer_class = ExternalToolSerializerV1
    v2_serializer_class = ExternalToolSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['get']

    def get_objects(self, request, **kwargs):
        return ExternalTool.objects.all()

    # @apispec_list_operation(
    #     'ExternalTool',
    #     summary="Get a list of registered tools",
    #     tags=["External Tools"]
    # )
    def get(self, request, **kwargs):
        return super(ExternalToolList, self).get(request, **kwargs)


class ExternalToolLaunch(BaseEntityDetailView):
    model = ExternalTool  # used by VersionedObjectMixin
    v1_serializer_class = ExternalToolLaunchSerializerV1
    v2_serializer_class = ExternalToolLaunchSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['get']

    def get_context_data(self, **kwargs):
        context = super(ExternalToolLaunch, self).get_context_data(**kwargs)
        context['tool_launch_context_id'] = self.request.query_params.get('context_id', None)
        return context

    def get_object(self, request, **kwargs):
        externaltool = super(ExternalToolLaunch, self).get_object(request, **kwargs)
        try:
            launchpoint = externaltool.get_launchpoint(kwargs.get('launchpoint'))
        except ExternalToolLaunchpoint.DoesNotExist:
            raise ValidationError(["Unknown launchpoint"])
        return launchpoint
