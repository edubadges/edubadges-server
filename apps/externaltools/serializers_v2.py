# # encoding: utf-8
#
#
# from django.urls import reverse
# from entity.serializers import DetailSerializerV2
# from externaltools.models import ExternalTool
# from mainsite.serializers import StripTagsCharField
# from mainsite.utils import OriginSetting
# from rest_framework import serializers
#
#
# class ExternalToolSerializerV2(DetailSerializerV2):
#     name = StripTagsCharField(max_length=254)
#     clientId = StripTagsCharField(max_length=254, source='client_id')
#
#     class Meta(DetailSerializerV2.Meta):
#         model = ExternalTool
#         # apispec_definition = ('ExternalTool', {})
#
#     def to_representation(self, instance):
#         representation = super(ExternalToolSerializerV2, self).to_representation(instance)
#         representation['launchpoints'] = {
#             lp.launchpoint: {
#                 "url": "{}{}".format(OriginSetting.HTTP, reverse("v2_api_externaltools_launch", kwargs=dict(
#                     launchpoint=lp.launchpoint,
#                     entity_id=lp.cached_externaltool.entity_id
#                 ))),
#                 "launchUrl": lp.launch_url,
#                 "label": lp.label,
#                 "iconUrl": lp.icon_url
#             } for lp in instance.cached_launchpoints()
#         }
#         return representation
#
#
# class ExternalToolLaunchSerializerV2(DetailSerializerV2):
#     launchUrl = serializers.URLField(source='launch_url')
#     launchData = serializers.DictField(source='generate_launch_data')