from collections import OrderedDict
from itertools import chain

from django.db import IntegrityError
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail
from rest_framework.serializers import PrimaryKeyRelatedField

from badgeuser.models import BadgeUser

from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.mixins import InternalValueErrorOverrideMixin
from mainsite.serializers import StripTagsCharField, BaseSlugRelatedField
from .models import Faculty, Institution, BadgeClassTag


class InstitutionSlugRelatedField(BaseSlugRelatedField):
    model = Institution


class FacultySlugRelatedField(BaseSlugRelatedField):
    model = Faculty


class BadgeClassTagSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255, required=True, allow_null=False, allow_blank=False)


class InstitutionSerializer(InternalValueErrorOverrideMixin, serializers.Serializer):
    description_english = StripTagsCharField(max_length=256, required=False, allow_null=True, allow_blank=True)
    description_dutch = StripTagsCharField(max_length=256, required=False, allow_null=True, allow_blank=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image_english = ValidImageField(required=False, allow_null=True)
    image_dutch = ValidImageField(required=False, allow_null=True)
    brin = serializers.CharField(read_only=True)
    name_english = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)
    name_dutch = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)
    grading_table = serializers.URLField(max_length=254, required=False, allow_null=True, allow_blank=True)
    award_allowed_institutions = PrimaryKeyRelatedField(many=True, queryset=Institution.objects.all(), required=False)
    linkedin_org_identifier = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)
    tags = BadgeClassTagSerializer(many=True, required=False)
    sis_default_user = PrimaryKeyRelatedField(many=False,
                                              queryset=BadgeUser.objects.filter(is_teacher=True),
                                              required=False)
    sis_integration_enabled = serializers.BooleanField(default=False, required=False)
    manage_client_id = serializers.CharField(max_length=254, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Institution

    def __init__(self, *args, **kwargs):
        super(InstitutionSerializer, self).__init__(*args, **kwargs)
        self.fields['sis_default_user'].queryset = BadgeUser.objects.filter(is_teacher=True)

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
        instance.linkedin_org_identifier = validated_data.get('linkedin_org_identifier')
        instance.manage_client_id = validated_data.get('manage_client_id')
        instance.sis_default_user = validated_data.get('sis_default_user')
        instance.sis_integration_enabled = validated_data.get('sis_integration_enabled')

        def is_deleted_tag(tag_list, tag):
            return not bool([t for t in tag_list if t["name"] == tag.name])

        def is_new_tag(tag_list, tag):
            return not bool([t for t in tag_list if t.name == tag["name"]])

        # can be persistent tags and transient tags (with possible the same name)
        tags = validated_data.get('tags', [])
        existing_tags = list(instance.badgeclasstag_set.all())
        deleted_tags = [tag for tag in existing_tags if is_deleted_tag(tags, tag)]
        new_tags = [tag for tag in tags if is_new_tag(existing_tags, tag)]
        for tag in deleted_tags:
            tag.delete()
        for tag in new_tags:
            new_tag = BadgeClassTag(name=tag["name"], institution=instance)
            new_tag.save()

        instance.award_allowed_institutions.set(validated_data.get('award_allowed_institutions', []))
        instance.save()
        return instance

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        institution = self.context['request'].user.institution
        if not data.get('name_english', False) and not data.get('name_dutch', False):
            e = OrderedDict([('name_english', [ErrorDetail('English or Dutch name is required', code=924)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict([('name_dutch', [ErrorDetail('Dutch or English name is required', code=912)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('image_english', False) and not data.get('image_dutch', False):
            e = OrderedDict([('image_english', [ErrorDetail('English or Dutch image is required', code=926)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict([('image_dutch', [ErrorDetail('Dutch or English image is required', code=918)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('description_english', False) and not data.get('description_dutch', False):
            e = OrderedDict(
                [('description_english', [ErrorDetail('English or Dutch description is required', code=925)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict(
                [('description_dutch', [ErrorDetail('Dutch or English description is required', code=913)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if institution.institution_type != 'MBO' and not data.get('grading_table', False):
            e = OrderedDict([('grading_table', [ErrorDetail('Grading Table is required', code=903)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors


class FacultySerializer(InternalValueErrorOverrideMixin, serializers.Serializer):
    id = serializers.ReadOnlyField()
    name_english = serializers.CharField(max_length=512, required=False, allow_null=True, allow_blank=True)
    name_dutch = serializers.CharField(max_length=512, required=False, allow_null=True, allow_blank=True)
    description_english = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    description_dutch = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    on_behalf_of = serializers.BooleanField(default=False, required=False)
    on_behalf_of_url = serializers.URLField(max_length=512, required=False, allow_null=True, allow_blank=True)
    on_behalf_of_display_name = serializers.CharField(max_length=512, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Faculty

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        if not data.get('name_english', False) and not data.get('name_dutch', False):
            e = OrderedDict([('name_english', [ErrorDetail('English or Dutch name is required', code=924)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict([('name_dutch', [ErrorDetail('English or Dutch name is required', code=912)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('description_english', False) and not data.get('description_dutch', False):
            e = OrderedDict(
                [('description_english', [ErrorDetail('English or Dutch description is required', code=925)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict(
                [('description_dutch', [ErrorDetail('English or Dutch description is required', code=913)])])
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
