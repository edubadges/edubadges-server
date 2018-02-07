# encoding: utf-8
from __future__ import unicode_literals

from apispec_drf.decorators import apispec_list_operation

from entity.api import BaseEntityListView
from externaltools.models import ExternalTool
from externaltools.serializers_v2 import ExternalToolSerializerV2
from mainsite.permissions import AuthenticatedWithVerifiedEmail


class ExternalToolList(BaseEntityListView):
    model = ExternalTool
    # v1_serializer_class = ExternalToolSerializerV1
    v2_serializer_class = ExternalToolSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['get']

    def get_objects(self, request, **kwargs):
        return ExternalTool.objects.all()

    @apispec_list_operation(
        'ExternalTool',
        summary="Get a list of registered tools",
        tags=["External Tools"]
    )
    def get(self, request, **kwargs):
        return super(ExternalToolList, self).get(request, **kwargs)


