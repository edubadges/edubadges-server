from django.db import IntegrityError
from rest_framework import serializers

from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.serializers import StripTagsCharField, BaseSlugRelatedField
from .models import Faculty, Institution


class InstitutionSlugRelatedField(BaseSlugRelatedField):
    model = Institution


class FacultySlugRelatedField(BaseSlugRelatedField):
    model = Faculty


class InstitutionSerializer(serializers.Serializer):
    description = StripTagsCharField(max_length=16384, required=False)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image = ValidImageField(required=False)
    grading_table = serializers.URLField(max_length=254, required=False)
    brin = serializers.CharField(max_length=254, required=False)

    class Meta:
        model = Institution

    def update(self, instance, validated_data):
        if instance.assertions:
            if validated_data.get('grading_table') and instance.grading_table != validated_data.get('grading_table'):
                raise BadgrValidationError(
                    {"grading_table": [{"error_code": 801,
                               "error_message": "Cannot change grading table, assertions have already been issued"}]})
            if validated_data.get('brin') and instance.brin != validated_data.get('brin'):
                raise BadgrValidationError(
                    {"brin": [{"error_code": 802,
                               "error_message": "Cannot change brin, assertions have already been issued"}]})
        instance.description = validated_data.get('description')
        if 'image' in validated_data:
            instance.image = validated_data.get('image')
        instance.grading_table = validated_data.get('grading_table')
        instance.brin = validated_data.get('brin')
        instance.save()
        return instance


class FacultySerializer(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(max_length=512)
    description = StripTagsCharField(max_length=16384, required=False)
    entity_id = StripTagsCharField(max_length=255, read_only=True)

    class Meta:
        model = Faculty

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.description = validated_data.get('description')
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
            BadgrValidationError(fields="You don't have the necessary permissions")
