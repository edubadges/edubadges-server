from rest_framework import serializers
from rest_framework.serializers import UUIDField
from .models import Faculty, Institution
from mainsite.serializers import StripTagsCharField


class InstitutionSerializerV1(serializers.Serializer):
    name = serializers.CharField(max_length=512)

    class Meta:
        model = Institution

class FacultySerializerV1(serializers.Serializer):
    name = serializers.CharField(max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')


    class Meta:
        model = Faculty
        
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.save()
        return instance
