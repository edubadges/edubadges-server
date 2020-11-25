from django.db import IntegrityError
from rest_framework import serializers

from badgeuser.serializers import TermsSerializer
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.serializers import StripTagsCharField, BaseSlugRelatedField
from .models import Faculty, Institution


class InstitutionSlugRelatedField(BaseSlugRelatedField):
    model = Institution


class FacultySlugRelatedField(BaseSlugRelatedField):
    model = Faculty


class InstitutionSerializer(serializers.Serializer):
    description_english = StripTagsCharField(max_length=256, required=True)
    description_dutch = StripTagsCharField(max_length=256, required=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image = ValidImageField(required=True)
    brin = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=254, required=True)
    grading_table = serializers.URLField(max_length=254, required=False)

    class Meta:
        model = Institution

    def update(self, instance, validated_data):
        instance.description_english = validated_data.get('description_english')
        instance.description_dutch = validated_data.get('description_dutch')
        if 'image' in validated_data:
            instance.image = validated_data.get('image')
        instance.grading_table = validated_data.get('grading_table')
        instance.name = validated_data.get('name')
        instance.save()
        return instance


class FacultySerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(max_length=512)
    description_english = StripTagsCharField(max_length=16384, required=False)
    description_dutch = StripTagsCharField(max_length=16384, required=False)
    entity_id = StripTagsCharField(max_length=255, read_only=True)

    class Meta:
        model = Faculty

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.description_english = validated_data.get('description_english')
        instance.description_dutch = validated_data.get('description_dutch')
        instance.save()
        return instance

    def create(self, validated_data, **kwargs):
        user_institution = self.context['request'].user.institution
        user_permissions = user_institution.get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            validated_data['institution'] = user_institution
            del validated_data['created_by']
            new_faculty = Faculty(**validated_data)
            try:
                new_faculty.save()
            except IntegrityError as e:
                raise serializers.ValidationError("Faculty name already exists")
            return new_faculty
        else:
            BadgrValidationError("You don't have the necessary permissions", 100)
