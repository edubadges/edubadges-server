from collections import OrderedDict
import os
import re
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator, EmailValidator, RegexValidator
from rest_framework import serializers

from badgeuser.models import BadgeUser
from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2, BaseSerializerV2
from issuer.models import Issuer, IssuerStaff, BadgeClass, BadgeInstance
from issuer.utils import generate_sha256_hashstring
from mainsite.drf_fields import ValidImageField
from mainsite.models import BadgrApp
from mainsite.serializers import (CachedUrlHyperlinkedRelatedField, StripTagsCharField, MarkdownCharField,
                                  HumanReadableBooleanField, OriginalJsonSerializerMixin)
from mainsite.validators import ChoicesValidator, TelephoneValidator, BadgeExtensionValidator


class IssuerAccessTokenSerializerV2(BaseSerializerV2):
    token = serializers.CharField()
    issuer = serializers.CharField()
    expires = serializers.DateTimeField()

    class Meta(DetailSerializerV2.Meta):
        apispec_definition = ('AccessToken', {})

    def to_representation(self, instance):
        return super(IssuerAccessTokenSerializerV2, self).to_representation(instance)


class IssuerStaffSerializerV2(DetailSerializerV2):
    user = EntityRelatedFieldV2(source='cached_user', queryset=BadgeUser.cached)
    role = serializers.CharField(validators=[ChoicesValidator(dict(IssuerStaff.ROLE_CHOICES).keys())])

    class Meta(DetailSerializerV2.Meta):
        apispec_definition = ('IssuerStaff', {
            'properties': {
                'role': {
                    'type': "string",
                    'enum': ["staff", "editor", "owner"]

                }
            }
        })


class IssuerSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=16384, required=False)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializerV2(many=True, source='staff_items', required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    class Meta(DetailSerializerV2.Meta):
        model = Issuer
        apispec_definition = ('Issuer', {
            'properties': OrderedDict([
                ('entityId', {
                    'type': "string",
                    'format': "string",
                    'description': "Unique identifier for this Issuer",
                }),
                ('entityType', {
                    'type': "string",
                    'format': "string",
                    'description': "\"Issuer\"",
                }),
                ('openBadgeId', {
                    'type': "string",
                    'format': "url",
                    'description': "URL of the OpenBadge compliant json",
                }),
                ('createdAt', {
                    'type': 'string',
                    'format': 'ISO8601 timestamp',
                    'description': "Timestamp when the Issuer was created",
                }),
                ('createdBy', {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "BadgeUser who created this Issuer",
                }),

                ('name', {
                    'type': "string",
                    'format': "string",
                    'description': "Name of the Issuer",
                }),
                ('image', {
                    'type': "string",
                    'format': "data:image/png;base64",
                    'description': "Base64 encoded string of an image that represents the Issuer",
                }),
                ('email', {
                    'type': "string",
                    'format': "email",
                    'description': "Contact email for the Issuer",
                }),
                ('url', {
                    'type': "string",
                    'format': "url",
                    'description': "Homepage or website associated with the Issuer",
                }),
                ('description', {
                    'type': "string",
                    'format': "text",
                    'description': "Short description of the Issuer",
                }),

            ])
        })

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data):
        staff = validated_data.pop('staff_items', [])
        new_issuer = super(IssuerSerializerV2, self).create(validated_data)

        # update staff after issuer is created
        new_issuer.staff_items = staff

        # set badgrapp
        new_issuer.badgrapp = BadgrApp.objects.get_current(self.context.get('request', None))

        return new_issuer


class AlignmentItemSerializerV2(BaseSerializerV2, OriginalJsonSerializerMixin):
    targetName = StripTagsCharField(source='target_name')
    targetUrl = serializers.URLField(source='target_url')
    targetDescription = StripTagsCharField(source='target_description', required=False, allow_null=True, allow_blank=True)
    targetFramework = StripTagsCharField(source='target_framework', required=False, allow_null=True, allow_blank=True)
    targetCode = StripTagsCharField(source='target_code', required=False, allow_null=True, allow_blank=True)

    class Meta:
        apispec_definition = ('BadgeClassAlignment', {
            'properties': {
            }
        })


class BadgeClassSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    issuer = EntityRelatedFieldV2(source='cached_issuer', required=False, queryset=Issuer.cached)
    issuerOpenBadgeId = serializers.URLField(source='issuer_jsonld_id', read_only=True)

    name = StripTagsCharField(max_length=1024)
    image = ValidImageField(required=False)
    description = StripTagsCharField(max_length=16384, required=True, convert_null=True)

    criteriaUrl = StripTagsCharField(source='criteria_url', required=False, allow_null=True, validators=[URLValidator()])
    criteriaNarrative = MarkdownCharField(source='criteria_text', required=False, allow_null=True)

    alignments = AlignmentItemSerializerV2(source='alignment_items', many=True, required=False)
    tags = serializers.ListField(child=StripTagsCharField(max_length=1024), source='tag_items', required=False)

    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    class Meta(DetailSerializerV2.Meta):
        model = BadgeClass
        apispec_definition = ('BadgeClass', {
            'properties': OrderedDict([
                ('entityId', {
                    'type': "string",
                    'format': "string",
                    'description': "Unique identifier for this BadgeClass",
                }),
                ('entityType', {
                    'type': "string",
                    'format': "string",
                    'description': "\"BadgeClass\"",
                }),
                ('openBadgeId', {
                    'type': "string",
                    'format': "url",
                    'description': "URL of the OpenBadge compliant json",
                }),
                ('createdAt', {
                    'type': 'string',
                    'format': 'ISO8601 timestamp',
                    'description': "Timestamp when the BadgeClass was created",
                }),
                ('createdBy', {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "BadgeUser who created this BadgeClass",
                }),

                ('issuer', {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "entityId of the Issuer who owns the BadgeClass",
                }),

                ('name', {
                    'type': "string",
                    'format': "string",
                    'description': "Name of the BadgeClass",
                }),
                ('description', {
                    'type': "string",
                    'format': "string",
                    'description': "Short description of the BadgeClass",
                }),
                ('image', {
                    'type': "string",
                    'format': "data:image/png;base64",
                    'description': "Base64 encoded string of an image that represents the BadgeClass.",
                }),
                ('criteriaUrl', {
                    'type': "string",
                    'format': "url",
                    'description': "External URL that describes in a human-readable format the criteria for the BadgeClass"
                }),
                ('criteriaNarrative', {
                    'type': "string",
                    'format': "markdown",
                    'description': "Markdown formatted description of the criteria"
                }),
                ('tags', {
                    'type': "array",
                    'items': {
                        'type': "string",
                        'format': "string"
                    },
                    'description': "List of tags that describe the BadgeClass"
                }),
                ('alignments', {
                    'type': "array",
                    'items': {
                        '$ref': '#/definitions/BadgeClassAlignment'
                    },
                    'description': "List of objects describing objectives or educational standards"
                }),
            ])
        })

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
    hashed = serializers.NullBooleanField(default=None, required=False)
    type = serializers.ChoiceField(
        choices=BadgeInstance.RECIPIENT_TYPE_CHOICES,
        default=BadgeInstance.RECIPIENT_TYPE_EMAIL,
        required=False,
        source='recipient_type'
    )
    plaintextIdentity = serializers.CharField(source='recipient_identifier', read_only=True, required=False)

    VALIDATORS = {
        BadgeInstance.RECIPIENT_TYPE_EMAIL: EmailValidator(),
        BadgeInstance.RECIPIENT_TYPE_URL: URLValidator(),
        BadgeInstance.RECIPIENT_TYPE_ID: URLValidator(),
        BadgeInstance.RECIPIENT_TYPE_TELEPHONE: TelephoneValidator(),
    }
    HASHED_DEFAULTS = {
        BadgeInstance.RECIPIENT_TYPE_EMAIL: True,
        BadgeInstance.RECIPIENT_TYPE_URL: False,
        BadgeInstance.RECIPIENT_TYPE_ID: False,
        BadgeInstance.RECIPIENT_TYPE_TELEPHONE: True,

    }

    def validate(self, attrs):
        recipient_type = attrs.get('recipient_type')
        recipient_identifier = attrs.get('recipient_identifier')
        hashed = attrs.get('hashed')
        if recipient_type in self.VALIDATORS:
            try:
                self.VALIDATORS[recipient_type](recipient_identifier)
            except DjangoValidationError as e:
                raise serializers.ValidationError(e.message)
        if hashed is None:
            attrs['hashed'] = self.HASHED_DEFAULTS.get(recipient_type, True)
        return attrs

    def to_representation(self, instance):
        representation = super(BadgeRecipientSerializerV2, self).to_representation(instance)
        if instance.hashed:
            representation['salt'] = instance.salt
            representation['identity'] = generate_sha256_hashstring(instance.recipient_identifier.lower(), instance.salt)

        return representation


class EvidenceItemSerializerV2(BaseSerializerV2, OriginalJsonSerializerMixin):
    url = serializers.URLField(source='evidence_url', max_length=1024, required=False)
    narrative = MarkdownCharField(required=False)

    class Meta:
        apispec_definition = ('AssertionEvidence', {
            'properties': OrderedDict([
                ('url', {
                    'type': "string",
                    'format': "url",
                    'description': "URL of a webpage presenting evidence of the achievement",
                }),
                ('narrative', {
                    'type': "string",
                    'format': "markdown",
                    'description': "Markdown narrative that describes the achievement",
                }),
            ])
        })

    def validate(self, attrs):
        if not (attrs.get('evidence_url', None) or attrs.get('narrative', None)):
            raise serializers.ValidationError("Either url or narrative is required")

        return attrs


class BadgeInstanceSerializerV2(DetailSerializerV2, OriginalJsonSerializerMixin):
    openBadgeId = serializers.URLField(source='jsonld_id', read_only=True)
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    badgeclass = EntityRelatedFieldV2(source='cached_badgeclass', required=False, queryset=BadgeClass.cached)
    badgeclassOpenBadgeId = CachedUrlHyperlinkedRelatedField(
        source='badgeclass_jsonld_id', view_name='badgeclass_json', lookup_field='entity_id',
        queryset=BadgeClass.cached, required=False)

    issuer = EntityRelatedFieldV2(source='cached_issuer', required=False, queryset=Issuer.cached)
    issuerOpenBadgeId = serializers.URLField(source='issuer_jsonld_id', read_only=True)

    image = serializers.FileField(read_only=True)
    recipient = BadgeRecipientSerializerV2(source='*')

    issuedOn = serializers.DateTimeField(source='issued_on', required=False)
    narrative = MarkdownCharField(required=False)
    evidence = EvidenceItemSerializerV2(many=True, required=False)

    revoked = HumanReadableBooleanField(read_only=True)
    revocationReason = serializers.CharField(source='revocation_reason', read_only=True)

    expires = serializers.DateTimeField(source='expires_at', required=False)

    notify = HumanReadableBooleanField(write_only=True, required=False, default=False)

    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    class Meta(DetailSerializerV2.Meta):
        model = BadgeInstance
        apispec_definition = ('Assertion', {
            'properties': OrderedDict([
                ('entityId', {
                    'type': "string",
                    'format': "string",
                    'description': "Unique identifier for this Assertion",
                }),
                ('entityType', {
                    'type': "string",
                    'format': "string",
                    'description': "\"Assertion\"",
                }),
                ('openBadgeId', {
                    'type': "string",
                    'format': "url",
                    'description': "URL of the OpenBadge compliant json",
                }),
                ('createdAt', {
                    'type': 'string',
                    'format': 'ISO8601 timestamp',
                    'description': "Timestamp when the Assertion was created",
                }),
                ('createdBy', {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "BadgeUser who created the Assertion",
                }),

                ('badgeclass', {
                    'type': 'string',
                    'format': 'entityId',
                    'description': "BadgeClass that issued this Assertion",
                }),
                ('badgeclassOpenBadgeId', {
                    'type': 'string',
                    'format': 'url',
                    'description': "URL of the BadgeClass to award",
                }),
                ('revoked', {
                    'type': 'boolean',
                    'description': "True if this Assertion has been revoked",
                }),
                ('revocationReason', {
                    'type': 'string',
                    'format': "string",
                    'description': "Short description of why the Assertion was revoked",
                }),

                ('image', {
                    'type': 'string',
                    'format': 'url',
                    'description': "URL to the baked assertion image",
                }),
                ('issuedOn', {
                    'type': 'string',
                    'format': 'ISO8601 timestamp',
                    'description': "Timestamp when the Assertion was issued",
                }),
                ('narrative', {
                    'type': 'string',
                    'format': 'markdown',
                    'description': "Markdown narrative of the achievement",
                }),
                ('evidence', {
                    'type': 'array',
                    'items': {
                        '$ref': '#/definitions/AssertionEvidence'
                    },
                    'description': "List of evidence associated with the achievement"
                }),
                ('recipient', {
                    'type': 'object',
                    'properties': OrderedDict([
                        ('identity', {
                            'type': 'string',
                            'format': 'string',
                            'description': 'Either the hash of the identity or the plaintext value'
                        }),
                        ('type', {
                            'type': 'string',
                            'enum': [c[0] for c in BadgeInstance.RECIPIENT_TYPE_CHOICES],
                            'description': "Type of identifier used to identify recipient"
                        }),
                        ('hashed', {
                            'type': 'boolean',
                            'description': "Whether or not the identity value is hashed."
                        }),
                        ('plaintextIdentity', {
                            'type': 'string',
                            'description': "The plaintext identity"
                        }),
                    ]),
                    'description': "Recipient that was issued the Assertion"
                }),
                ('expires', {
                    'type': 'string',
                    'format': 'ISO8601 timestamp',
                    'description': "Timestamp when the Assertion expires",
                }),
            ])
        })

    def update(self, instance, validated_data):
        # BadgeInstances are not updatable
        return instance

    def validate(self, data):
        if 'cached_badgeclass' in data and 'badgeclass_jsonld_id' in data:
            raise serializers.ValidationError(
                {"badgeclass": ["Only one of badgeclass and badgeclassOpenBadgeId allowed."]})

        if 'cached_badgeclass' in data:
            # included badgeclass in request
            data['badgeclass'] = data.pop('cached_badgeclass')
        elif 'badgeclass' in self.context:
            # badgeclass was passed in context
            data['badgeclass'] = self.context.get('badgeclass')
        elif 'badgeclass_jsonld_id' in data:
            data['badgeclass'] = data.pop('badgeclass_jsonld_id')
        else:
            # badgeclass is required on create
            raise serializers.ValidationError({"badgeclass": ["This field is required"]})

        expected_issuer = self.context.get('kwargs', {}).get('issuer')
        if expected_issuer and data['badgeclass'].issuer != expected_issuer:
            raise serializers.ValidationError({"badgeclass": ["Could not find matching badgeclass for this issuer."]})

        data['issuer'] = data['badgeclass'].issuer
        return data
