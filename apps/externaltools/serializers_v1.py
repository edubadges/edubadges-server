# encoding: utf-8


from django.urls import reverse
from mainsite.serializers import StripTagsCharField
from mainsite.utils import OriginSetting
from rest_framework import serializers


class ExternalToolSerializerV1(serializers.Serializer):
    name = StripTagsCharField(max_length=254)
    client_id = StripTagsCharField(max_length=254)
    slug = StripTagsCharField(max_length=255, source='entity_id', read_only=True)

    def to_representation(self, instance):
        representation = super(ExternalToolSerializerV1, self).to_representation(instance)
        representation['launchpoints'] = {
            lp.launchpoint: {
                "url": "{}{}".format(OriginSetting.HTTP, reverse("v1_api_externaltools_launch", kwargs=dict(
                    launchpoint=lp.launchpoint,
                    slug=lp.cached_externaltool.entity_id
                ))),
                "launch_url": lp.launch_url,
                "label": lp.label,
                "icon_url": lp.icon_url
            } for lp in instance.cached_launchpoints()
        }
        return representation


class ExternalToolLaunchSerializerV1(serializers.Serializer):
    launch_url = serializers.URLField()

    def to_representation(self, instance):
        representation = super(ExternalToolLaunchSerializerV1, self).to_representation(instance)
        requesting_user = self.context['request'].user if 'request' in self.context else None
        context_id = self.context.get('tool_launch_context_id', None)
        representation['launch_data'] = instance.generate_launch_data(user=requesting_user, context_id=context_id)

        return representation
