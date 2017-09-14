import uuid

import os
from django.core.validators import URLValidator
from rest_framework import serializers

from badgeuser.models import BadgeUser
from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2, BaseSerializerV2
from issuer.models import Issuer, IssuerStaff, BadgeClass, BadgeInstance
from mainsite.drf_fields import ValidImageField
from mainsite.serializers import StripTagsCharField, MarkdownCharField, HumanReadableBooleanField, \
    OriginalJsonSerializerMixin
from mainsite.validators import ChoicesValidator


class IssuerStaffSerializerV2(DetailSerializerV2):
    user = EntityRelatedFieldV2(source='cached_user', queryset=BadgeUser.cached)
    role = serializers.CharField(validators=[ChoicesValidator(dict(IssuerStaff.ROLE_CHOICES).keys())])

    class Meta:
        apispec_definition = ('IssuerStaff', {
            'properties': {
                'role': {
                    'type': "string",
                    'enum': ["staff", "editor", "owner"]

                }
            }
        })


class IssuerSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True, help_text="The url to find the Open Badge")
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=1024, required=True)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializerV2(many=True, source='staff_items', required=False)

    class Meta(DetailSerializerV2.Meta):
        model = Issuer
        apispec_definition = ('Issuer', {
            'properties': {
                'createdBy': {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "entityId of the BadgeUser who created this issuer",
                }
            }
        })

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


class AlignmentItemSerializerV2(BaseSerializerV2, OriginalJsonSerializerMixin):
    targetName = serializers.CharField(source='target_name')
    targetUrl = serializers.URLField(source='target_url')
    targetDescription = serializers.URLField(source='target_description', required=False)
    targetFramework = serializers.URLField(source='target_framework', required=False)
    targetCode = serializers.URLField(source='target_code', required=False)


class BadgeClassSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    issuer = EntityRelatedFieldV2(source='cached_issuer', required=False, queryset=Issuer.cached)

    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    description = StripTagsCharField(max_length=1024, required=True)

    criteriaUrl = StripTagsCharField(source='criteria_url', required=False, allow_null=True, validators=[URLValidator()])
    criteriaNarrative = MarkdownCharField(source='criteria_text', required=False, allow_null=True)

    alignment = AlignmentItemSerializerV2(many=True, required=False)

    class Meta(DetailSerializerV2.Meta):
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
    type = serializers.CharField(default='email', required=False, source='recipient_type')


class EvidenceItemSerializerV2(BaseSerializerV2, OriginalJsonSerializerMixin):
    url = serializers.URLField(source='evidence_url', max_length=1024, required=False)
    narrative = MarkdownCharField(required=False)

    def validate(self, attrs):
        if not (attrs.get('evidence_url', None) or attrs.get('narrative', None)):
            raise serializers.ValidationError("Either url or narrative is required")

        return attrs


class BadgeInstanceSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    badgeclass = EntityRelatedFieldV2(source='cached_badgeclass', required=False, queryset=BadgeClass.cached)

    image = serializers.FileField(read_only=True)
    recipient = BadgeRecipientSerializerV2(source='*')

    issuedOn = serializers.DateTimeField(source='issued_on', required=False)
    narrative = MarkdownCharField(required=False)
    evidence = EvidenceItemSerializerV2(many=True, required=False)

    revoked = HumanReadableBooleanField(read_only=True)
    revocationReason = serializers.CharField(source='revocation_reason', read_only=True)
    
    class Meta(DetailSerializerV2.Meta):
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


        validated_data['issuer'] = validated_data['badgeclass'].issuer


        return super(BadgeInstanceSerializerV2, self).create(validated_data)

