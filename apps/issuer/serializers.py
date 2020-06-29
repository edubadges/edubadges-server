import json
import os
import uuid
import datetime
from collections import OrderedDict
from itertools import chain

from django.apps import apps
from django.core.validators import URLValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from badgeuser.serializers import BadgeUserIdentifierField
from institution.serializers import FacultySlugRelatedField
from lti_edu.models import StudentsEnrolled
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.models import BadgrApp
from mainsite.serializers import HumanReadableBooleanField, StripTagsCharField, MarkdownCharField, \
    OriginalJsonSerializerMixin, BaseSlugRelatedField
from mainsite.utils import OriginSetting
from mainsite.validators import BadgeExtensionValidator
from . import utils
from .models import Issuer, BadgeClass, BadgeInstance, BadgeClassExtension, IssuerExtension


class IssuerSlugRelatedField(BaseSlugRelatedField):
    model = Issuer


class BadgeClassSlugRelatedField(BaseSlugRelatedField):
    model = BadgeClass


class PeriodField(serializers.Field):
    """Period represented in days"""

    def to_internal_value(self, value):
        return datetime.timedelta(days=value)

    def to_representation(self, value):
        return value.days


class ExtensionsSaverMixin(object):
    def remove_extensions(self, instance, extensions_to_remove):
        extensions = instance.cached_extensions()
        for ext in extensions:
            if ext.name in extensions_to_remove:
                ext.delete()

    def update_extensions(self, instance, extensions_to_update, received_extension_items):
        current_extensions = instance.cached_extensions()
        for ext in current_extensions:
            if ext.name in extensions_to_update:
                new_values = received_extension_items[ext.name]
                ext.original_json = json.dumps(new_values)
                ext.save()

    def save_extensions(self, validated_data, instance):
        if validated_data.get('extensions', False):
            extension_items = validated_data.pop('extensions')
            received_extensions = list(extension_items.keys())
            current_extension_names = list(instance.extension_items.keys())
            remove_these_extensions = set(current_extension_names) - set(received_extensions)
            update_these_extensions = set(current_extension_names).intersection(set(received_extensions))
            add_these_extensions = set(received_extensions) - set(current_extension_names)
            self.remove_extensions(instance, remove_these_extensions)
            self.update_extensions(instance, update_these_extensions, extension_items)
            self.add_extensions(instance, add_these_extensions, extension_items)


class IssuerSerializer(OriginalJsonSerializerMixin, ExtensionsSaverMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name = StripTagsCharField(max_length=1024)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=16384, required=False)
    url = serializers.URLField(max_length=1024, required=True)
    faculty = FacultySlugRelatedField(slug_field='entity_id', required=True)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    class Meta:
        apispec_definition = ('Issuer', {})

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['faculty'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            new_issuer = Issuer(**validated_data)
            # set badgrapp
            new_issuer.badgrapp = BadgrApp.objects.get_current(self.context.get('request', None))
            new_issuer.save()
            return new_issuer
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)

    def update(self, instance, validated_data):
        if instance.assertions:
            raise BadgrValidationError("Cannot change any value, assertions have already been issued within this entity", 214)
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        self.save_extensions(validated_data, instance)
        if not instance.badgrapp_id:
            instance.badgrapp = BadgrApp.objects.get_current(self.context.get('request', None))
        instance.save()
        return instance

    def to_representation(self, obj):
        representation = super(IssuerSerializer, self).to_representation(obj)
        representation['json'] = obj.get_json(obi_version='1_1', use_canonical_id=True)

        if self.context.get('embed_badgeclasses', False):
            representation['badgeclasses'] = BadgeClassSerializer(obj.badgeclasses.all(), many=True,
                                                                  context=self.context).data
        return representation

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = IssuerExtension(name=extension_name,
                                        original_json=json.dumps(original_json),
                                        issuer_id=instance.pk)
            extension.save()


class AlignmentItemSerializer(serializers.Serializer):
    target_name = StripTagsCharField()
    target_url = serializers.URLField()
    target_description = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_framework = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_code = StripTagsCharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        apispec_definition = ('BadgeClassAlignment', {})


class BadgeClassSerializer(OriginalJsonSerializerMixin, ExtensionsSaverMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name = StripTagsCharField(max_length=255)
    image = ValidImageField(required=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)
    criteria = MarkdownCharField(allow_blank=True, required=False, write_only=True)
    criteria_text = MarkdownCharField(required=False, allow_null=True, allow_blank=True)
    criteria_url = StripTagsCharField(required=False, allow_blank=True, allow_null=True, validators=[URLValidator()])
    description = StripTagsCharField(max_length=16384, required=True, convert_null=True)
    alignment = AlignmentItemSerializer(many=True, source='alignment_items', required=False)
    tags = serializers.ListField(child=StripTagsCharField(max_length=1024), source='tag_items', required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])
    expiration_period = PeriodField(required=False)

    class Meta:
        apispec_definition = ('BadgeClass', {})

    def get_expiration_period(self, instance):
        if instance.expiration_period:
            return instance.expiration_period.days

    def to_representation(self, instance):
        representation = super(BadgeClassSerializer, self).to_representation(instance)
        representation['issuer'] = OriginSetting.HTTP + reverse('issuer_json',
                                                                kwargs={'entity_id': instance.cached_issuer.entity_id})
        representation['json'] = instance.get_json(obi_version='1_1', use_canonical_id=True)
        return representation

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_badgeclass_' + str(uuid.uuid4()) + img_ext
        return image

    def validate_criteria_text(self, criteria_text):
        if criteria_text is not None and criteria_text != '':
            return criteria_text
        else:
            return None

    def validate_criteria_url(self, criteria_url):
        if criteria_url is not None and criteria_url != '':
            return criteria_url
        else:
            return None

    def validate_name(self, name):
        return strip_tags(name)

    def validate_description(self, description):
        return strip_tags(description)

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = BadgeClassExtension(name=extension_name,
                                            original_json=json.dumps(original_json),
                                            badgeclass_id=instance.pk)
            extension.save()

    def update(self, instance, validated_data):
        if instance.assertions:
            raise BadgrValidationError(
                fields={"instance": [{"error_code": 999,
                                      "error_message": "Cannot change any value, assertions have already been issued"}]})
        self.save_extensions(validated_data, instance)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def to_internal_value(self, data):
        errors = OrderedDict()
        if not data.get('criteria_text', False) and not data.get('criteria_url', False):
            e = OrderedDict([('criteria_text', [ErrorDetail('Either criteria_url or criteria_text is required')]),
                             ('criteria_url', [ErrorDetail('Either criteria_url or criteria_text is required')])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if data.get('criteria_url', False):
            if not utils.is_probable_url(data.get('criteria_url')):
                e = OrderedDict([('criteria_url', [ErrorDetail('Must be a proper url.')])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        if errors:
            try:
                super(BadgeClassSerializer, self).to_internal_value(data)
                raise serializers.ValidationError(detail=errors)
            except serializers.ValidationError as e:
                e.detail = OrderedDict(chain(e.detail.items(), errors.items()))
                raise e
        else:
            return super(BadgeClassSerializer, self).to_internal_value(data)

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['issuer'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            new_badgeclass = BadgeClass.objects.create(**validated_data)
            return new_badgeclass
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)


class BadgeInstanceSerializer(OriginalJsonSerializerMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField(read_only=True)
    entity_id = serializers.CharField(max_length=255, read_only=True)
    image = serializers.FileField(read_only=True)  # use_url=True, might be necessary
    email = serializers.EmailField(max_length=1024, required=False, write_only=True)
    recipient_identifier = serializers.CharField(max_length=1024, required=False)
    recipient_email = serializers.SerializerMethodField()
    recipient_name = serializers.SerializerMethodField()
    recipient_type = serializers.CharField(default=BadgeInstance.RECIPIENT_TYPE_EDUID)
    allow_uppercase = serializers.BooleanField(default=False, required=False, write_only=True)

    revoked = HumanReadableBooleanField(read_only=True)
    revocation_reason = serializers.CharField(read_only=True)

    expires = serializers.DateTimeField(source='expires_at', required=False, allow_null=True)
    issue_signed = serializers.BooleanField(required=False)
    signing_password = serializers.CharField(max_length=1024, required=False)
    enrollment_entity_id = serializers.CharField(max_length=1024, required=False)

    create_notification = HumanReadableBooleanField(write_only=True, required=False, default=False)

    hashed = serializers.NullBooleanField(default=None, required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    class Meta:
        apispec_definition = ('Assertion', {})

    def get_recipient_email(self, obj):
        return obj.get_email_address()

    def get_recipient_name(self, obj):
        return obj.get_recipient_name()

    def validate(self, data):
        if data.get('email') and not data.get('recipient_identifier'):
            data['recipient_identifier'] = data.get('email')

        hashed = data.get('hashed', None)
        if hashed is None:
            recipient_type = data.get('recipient_type')
            if recipient_type in (BadgeInstance.RECIPIENT_TYPE_URL, BadgeInstance.RECIPIENT_TYPE_ID):
                data['hashed'] = False
            else:
                data['hashed'] = True

        return data

    def validate_narrative(self, data):
        if data is None or data == "":
            return None
        else:
            return data

    def to_representation(self, instance):
        # if self.context.get('extended_json'):
        #     self.fields['json'] = V1InstanceSerializer(source='extended_json')

        representation = super(BadgeInstanceSerializer, self).to_representation(instance)
        representation['json'] = instance.get_json(obi_version="1_1", use_canonical_id=True)
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializer(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = OriginSetting.HTTP + reverse('issuer_json', kwargs={
                'entity_id': instance.cached_issuer.entity_id})
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializer(instance.cached_badgeclass,
                                                                 context=self.context).data
        else:
            representation['badge_class'] = OriginSetting.HTTP + reverse('badgeclass_json', kwargs={
                'entity_id': instance.cached_badgeclass.entity_id})

        representation['public_url'] = OriginSetting.HTTP + reverse('badgeinstance_json',
                                                                    kwargs={'entity_id': instance.entity_id})

        if apps.is_installed('badgebook'):
            try:
                from badgebook.models import BadgeObjectiveAward
                from badgebook.serializers import BadgeObjectiveAwardSerializer
                try:
                    award = BadgeObjectiveAward.cached.get(badge_instance_id=instance.id)
                except BadgeObjectiveAward.DoesNotExist:
                    representation['award'] = None
                else:
                    representation['award'] = BadgeObjectiveAwardSerializer(award).data
            except ImportError:
                pass

        return representation

    def create(self, validated_data):
        """
        Requires self.context to include request (with authenticated request.user)
        and badgeclass: issuer.models.BadgeClass.
        """
        badgeclass = self.context['request'].data.get('badgeclass')
        enrollment = StudentsEnrolled.objects.get(entity_id=validated_data.get('enrollment_entity_id'))
        expires_at = None
        if badgeclass.expiration_period:
            expires_at = datetime.datetime.now().replace(microsecond=0, second=0, minute=0, hour=0) + badgeclass.expiration_period
        if enrollment.badge_instance:
            raise BadgrValidationError("Can't award enrollment, it has already been awarded", 213)
        if self.context['request'].data.get('issue_signed', False):
            assertion = badgeclass.issue_signed(
                recipient=enrollment.user,
                created_by=self.context.get('request').user,
                allow_uppercase=validated_data.get('allow_uppercase'),
                recipient_type=validated_data.get('recipient_type', BadgeInstance.RECIPIENT_TYPE_EDUID),
                badgr_app=BadgrApp.objects.get_current(self.context.get('request')),
                expires_at=expires_at,
                extensions=validated_data.get('extension_items', None),
                identifier=uuid.uuid4().urn,
                signer=validated_data.get('created_by'),
            )
        else:
            assertion = badgeclass.issue(
                recipient=enrollment.user,
                notify=self.context['request'].data.get('create_notification'),
                created_by=self.context.get('request').user,
                allow_uppercase=validated_data.get('allow_uppercase'),
                recipient_type=validated_data.get('recipient_type', BadgeInstance.RECIPIENT_TYPE_EDUID),
                badgr_app=BadgrApp.objects.get_current(self.context.get('request')),
                expires_at=expires_at,
                extensions=validated_data.get('extension_items', None)
            )

        enrollment.date_awarded = timezone.now()
        enrollment.badge_instance = assertion
        enrollment.save()
        enrollment.user.remove_cached_data(['cached_pending_enrollments'])
        return assertion

    def update(self, instance, validated_data):
        updateable_fields = [
            'evidence_items',
            'expires_at',
            'extension_items',
            'hashed',
            'issued_on',
            'recipient_identifier',
            'recipient_type'
        ]

        for field_name in updateable_fields:
            if field_name in validated_data:
                setattr(instance, field_name, validated_data.get(field_name))
        instance.rebake(save=False)
        instance.save()

        return instance
