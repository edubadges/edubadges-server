import uuid

import os
from django.core.validators import URLValidator
from rest_framework import serializers

from badgeuser.models import BadgeUser
from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2
from mainsite.drf_fields import ValidImageField
from mainsite.serializers import StripTagsCharField, MarkdownCharField
from mainsite.validators import ChoicesValidator
from issuer.models import Issuer, IssuerStaff, BadgeClass


class IssuerStaffSerializerV2(DetailSerializerV2):
    user = EntityRelatedFieldV2(source='cached_user', queryset=BadgeUser.cached)
    role = serializers.CharField(validators=[ChoicesValidator(dict(IssuerStaff.ROLE_CHOICES).keys())])


class IssuerSerializerV2(DetailSerializerV2):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=1024, required=True)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializerV2(many=True, source='staff_items', required=False)

    class Meta:
        model = Issuer

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data):
        staff = validated_data.pop('staff_items')
        new_issuer = super(IssuerSerializerV2, self).create(validated_data)

        # update staff after issuer is created
        new_issuer.staff_items = staff

        return new_issuer


class BadgeClassSerializerV2(DetailSerializerV2):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    issuer = EntityRelatedFieldV2(source='cached_issuer', required=False, queryset=Issuer.cached)

    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    description = StripTagsCharField(max_length=1024, required=True)

    criteriaUrl = StripTagsCharField(source='criteria_url', required=False, validators=[URLValidator()])
    criteriaNarrative = MarkdownCharField(source='criteria_text', required=False)

    class Meta:
        model = BadgeClass

    def update(self, instance, validated_data):
        if 'cached_issuer' in validated_data:
            validated_data.pop('cached_issuer')  # issuer is not updatable
        return super(BadgeClassSerializerV2, self).update(instance, validated_data)

    def create(self, validated_data):
        if 'cached_issuer' in validated_data:
            # included issuer reference
            validated_data['issuer'] = validated_data.pop('cached_issuer')
        elif 'issuer' in self.context:
            # issuer was passed in context
            validated_data['issuer'] = self.context.get('issuer')
        else:
            # issuer is required on create
            raise serializers.ValidationError({"issuer": "This field is required"})

        return super(BadgeClassSerializerV2, self).create(validated_data)

