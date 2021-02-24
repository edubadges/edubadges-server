from django.db import IntegrityError
from rest_framework import serializers
from collections import OrderedDict
from itertools import chain
from rest_framework.exceptions import ErrorDetail

from badgeuser.serializers import TermsSerializer
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.mixins import InternalValueErrorOverrideMixin
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


class FacultySerializer(InternalValueErrorOverrideMixin, serializers.Serializer):
    id = serializers.ReadOnlyField()
    name_english = serializers.CharField(max_length=512, required=False, allow_null=True, allow_blank=True)
    name_dutch = serializers.CharField(max_length=512, required=False, allow_null=True, allow_blank=True)
    description_english = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    description_dutch = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)

    class Meta:
        model = Faculty

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        if not data.get('name_english', False) and not data.get('name_dutch', False):
            e = OrderedDict([('name_english', [ErrorDetail('Either Dutch or English name is required', code=912)]),
                             ('name_dutch', [ErrorDetail('Either Dutch or English name is required', code=912)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('description_english', False) and not data.get('description_dutch', False):
            e = OrderedDict([('description_english', [ErrorDetail('Either Dutch or English description is required', code=913)]),
                             ('description_dutch', [ErrorDetail('Either Dutch or English description is required', code=913)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
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
