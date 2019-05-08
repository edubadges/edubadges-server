from django.contrib.auth.models import Group
from rest_framework import serializers

from mainsite.serializers import StripTagsCharField


class GroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')

    class Meta:
        model = Group
        fields = ('name', 'slug')

    def to_representation(self, instance):
        return  super(GroupSerializer, self).to_representation(instance)