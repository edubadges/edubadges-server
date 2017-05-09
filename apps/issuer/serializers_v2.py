import uuid

import os
from django.core.validators import URLValidator
from rest_framework import serializers

from badgeuser.models import BadgeUser
from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2, BaseSerializerV2
from mainsite.drf_fields import ValidImageField
from mainsite.serializers import StripTagsCharField, MarkdownCharField, HumanReadableBooleanField
from mainsite.validators import ChoicesValidator
from issuer.models import Issuer, IssuerStaff, BadgeClass, BadgeInstance


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

    criteriaUrl = StripTagsCharField(source='criteria_url', required=False, allow_null=True, validators=[URLValidator()])
    criteriaNarrative = MarkdownCharField(source='criteria_text', required=False, allow_null=True)

    class Meta:
        model = BadgeClass

    def update(self, instance, validated_data):
        if 'cached_issuer' in validated_data:
            validated_data.pop('cached_issuer')  # issuer is not updatable
        return super(BadgeClassSerializerV2, self).update(instance, validated_data)

    def create(self, validated_data):
        if 'cached_issuer' in validated_data:
            # included issuer in request
            validated_data['issuer'] = validated_data.pop('cached_issuer')
        elif 'issuer' in self.context:
            # issuer was passed in context
            validated_data['issuer'] = self.context.get('issuer')
        else:
            # issuer is required on create
            raise serializers.ValidationError({"issuer": "This field is required"})

        return super(BadgeClassSerializerV2, self).create(validated_data)


class BadgeRecipientSerializerV2(BaseSerializerV2):
    identity = serializers.CharField(source='recipient_identifier')
    type = serializers.CharField(default='email', required=False)


class EvidenceItemSerializerV2(BaseSerializerV2):
    url = serializers.URLField(source='evidence_url', max_length=1024, required=False)
    narrative = MarkdownCharField(required=False)

    def validate(self, attrs):
        if not (attrs.get('url', None) or attrs.get('narrative', None)):
            raise serializers.ValidationError("Either url or narrative is required")


class BadgeInstanceSerializerV2(DetailSerializerV2):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    badgeclass = EntityRelatedFieldV2(source='cached_badgeclass', required=False, queryset=BadgeClass.cached)

    image = serializers.FileField(read_only=True)
    recipient = BadgeRecipientSerializerV2(source='*')

    issuedOn = serializers.DateTimeField(source='created_at', read_only=True)
    narrative = MarkdownCharField(required=False)
    evidence = EvidenceItemSerializerV2(many=True, required=False)

    revoked = HumanReadableBooleanField(read_only=True)
    revocationReason = serializers.CharField(source='revocation_reason', read_only=True)
    
    class Meta:
        model = BadgeInstance
        
    def update(self, instance, validated_data):
        # BadgeInstances are not updatable
        return instance
    
    def create(self, validated_data):
        if 'cached_badgeclass' in validated_data:
            # included badgeclass in request
            validated_data['badgeclass'] = validated_data.pop('cached_badgeclass')
        elif 'badgeclass' in self.context:
            # badgeclass was passed in context
            validated_data['badgeclass'] = self.context.get('badgeclass')
        else:
            # badgeclass is required on create
            raise serializers.ValidationError({"badgeclass": "This field is required"})

        return super(BadgeInstanceSerializerV2, self).create(validated_data)
