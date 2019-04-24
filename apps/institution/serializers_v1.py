from django.db import IntegrityError
from rest_framework import serializers
from .models import Faculty, Institution
from mainsite.serializers import StripTagsCharField


class InstitutionSerializerV1(serializers.Serializer):
    name = serializers.CharField(max_length=512)

    class Meta:
        model = Institution

class FacultySerializerV1(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')


    class Meta:
        model = Faculty
        
    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.save()
        return instance

    def create(self, validated_data, **kwargs):
        user_institution = self.context['request'].user.institution
        validated_data['institution'] = user_institution
        del validated_data['created_by']
        new_faculty = Faculty(**validated_data)
        try:
            new_faculty.save()
        except IntegrityError as e:
            raise serializers.ValidationError("Faculty name already exists")
        return new_faculty
