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


class InstitutionSerializer(InternalValueErrorOverrideMixin, serializers.Serializer):
    description_english = StripTagsCharField(max_length=256, required=False, allow_null=True, allow_blank=True)
    description_dutch = StripTagsCharField(max_length=256, required=False, allow_null=True, allow_blank=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image_english = ValidImageField(required=False, allow_null=True)
    image_dutch = ValidImageField(required=False, allow_null=True)
    brin = serializers.CharField(read_only=True)
    name_english = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)
    name_dutch = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)
    grading_table = serializers.URLField(max_length=254, required=False)

    class Meta:
        model = Institution

    def update(self, instance, validated_data):
        instance.description_english = validated_data.get('description_english')
        instance.description_dutch = validated_data.get('description_dutch')
        if 'image_english' in validated_data:
            instance.image_english = validated_data.get('image_english')
        if 'image_dutch' in validated_data:
            instance.image_dutch = validated_data.get('image_dutch')
        instance.grading_table = validated_data.get('grading_table')
        instance.name_english = validated_data.get('name_english')
        instance.name_dutch = validated_data.get('name_dutch')
        instance.save()
        return instance

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        institution = self.context['request'].user.institution
        if institution.default_language == institution.DEFAULT_LANGUAGE_ENGLISH:
            if not data.get('name_english', False):
                e = OrderedDict([('name_english', [ErrorDetail('English name is required', code=924)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('image_english', False):
                e = OrderedDict([('image_english', [ErrorDetail('English image is required', code=926)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('description_english', False):
                e = OrderedDict([('description_english', [ErrorDetail('English description is required', code=925)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        if institution.default_language == institution.DEFAULT_LANGUAGE_DUTCH:
            if not data.get('name_dutch', False):
                e = OrderedDict([('name_dutch', [ErrorDetail('Dutch name is required', code=912)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('image_dutch', False):
                e = OrderedDict([('image_dutch', [ErrorDetail('Dutch image is required', code=918)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('description_dutch', False):
                e = OrderedDict([('description_dutch', [ErrorDetail('Dutch description is required', code=913)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        return errors


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
        institution = self.context['request'].user.institution
        if institution.default_language == institution.DEFAULT_LANGUAGE_ENGLISH:
            if not data.get('name_english', False):
                e = OrderedDict([('name_english', [ErrorDetail('English name is required', code=924)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('description_english', False):
                e = OrderedDict([('description_english', [ErrorDetail('English description is required', code=925)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        if institution.default_language == institution.DEFAULT_LANGUAGE_DUTCH:
            if not data.get('name_dutch', False):
                e = OrderedDict([('name_dutch', [ErrorDetail('Dutch name is required', code=912)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
            if not data.get('description_dutch', False):
                e = OrderedDict([('description_dutch', [ErrorDetail('Dutch description is required', code=913)])])
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
