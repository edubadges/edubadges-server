# encoding: utf-8
from __future__ import unicode_literals

from entity.serializers import DetailSerializerV2
from externaltools.models import ExternalTool
from mainsite.serializers import StripTagsCharField


class ExternalToolSerializerV2(DetailSerializerV2):
    name = StripTagsCharField(max_length=254)
    clientId = StripTagsCharField(max_length=254, source='client_id')

    class Meta(DetailSerializerV2.Meta):
        model = ExternalTool

    def to_representation(self, instance):
        representation = super(ExternalToolSerializerV2, self).to_representation(instance)
        representation['launchpoints'] = {
            lp.launchpoint: {
                "url": lp.launch_url,
                "label": lp.label,
                "iconUrl": lp.icon_url
            } for lp in instance.cached_launchpoints()
        }
        return representation
