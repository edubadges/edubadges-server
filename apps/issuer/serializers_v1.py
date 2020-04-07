import json
import os
import uuid

from badgeuser.serializers_v1 import BadgeUserIdentifierFieldV1
from django.apps import apps
from django.core.validators import URLValidator
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from lti_edu.models import StudentsEnrolled
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError
from mainsite.models import BadgrApp
from mainsite.serializers import HumanReadableBooleanField, StripTagsCharField, MarkdownCharField, \
    OriginalJsonSerializerMixin, BaseSlugRelatedField
from mainsite.utils import OriginSetting
from rest_framework import serializers

from institution.serializers import FacultySlugRelatedField

from . import utils
from .models import Issuer, BadgeClass, BadgeInstance, BadgeClassExtension, IssuerExtension


class IssuerSlugRelatedField(BaseSlugRelatedField):
    model = Issuer


class BadgeClassSlugRelatedField(BaseSlugRelatedField):
    model = BadgeClass


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
        extension_items = validated_data.get('extension_items')
        received_extensions = list(extension_items.keys())
        current_extension_names = list(instance.extension_items.keys())
        remove_these_extensions = set(current_extension_names) - set(received_extensions)
        update_these_extensions = set(current_extension_names).intersection(set(received_extensions))
        add_these_extensions = set(received_extensions) - set(current_extension_names)
        self.remove_extensions(instance, remove_these_extensions)
        self.update_extensions(instance, update_these_extensions, extension_items)
        self.add_extensions(instance, add_these_extensions, extension_items)


class IssuerSerializerV1(OriginalJsonSerializerMixin, ExtensionsSaverMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1()
    name = StripTagsCharField(max_length=1024)
    slug = StripTagsCharField(max_length=255, source='entity_id', read_only=True)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=16384, required=False)
    url = serializers.URLField(max_length=1024, required=True)
    faculty = FacultySlugRelatedField(slug_field='entity_id', required=True)
    extensions = serializers.DictField(source='extension_items', required=False)

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
            raise BadgrValidationError(fields="You don't have the necessary permissions")

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]

        if not instance.badgrapp_id:
            instance.badgrapp = BadgrApp.objects.get_current(self.context.get('request', None))

        instance.save()
        return instance

    def to_representation(self, obj):
        representation = super(IssuerSerializerV1, self).to_representation(obj)
        representation['json'] = obj.get_json(obi_version='1_1', use_canonical_id=True)

        if self.context.get('embed_badgeclasses', False):
            representation['badgeclasses'] = BadgeClassSerializerV1(obj.badgeclasses.all(), many=True,
                                                                    context=self.context).data
        return representation

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = IssuerExtension(name=extension_name,
                                        original_json=json.dumps(original_json),
                                        issuer_id=instance.pk)
            extension.save()


class AlignmentItemSerializerV1(serializers.Serializer):
    target_name = StripTagsCharField()
    target_url = serializers.URLField()
    target_description = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_framework = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_code = StripTagsCharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        apispec_definition = ('BadgeClassAlignment', {})


class BadgeClassSerializerV1(OriginalJsonSerializerMixin, ExtensionsSaverMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1()
    id = serializers.IntegerField(required=False, read_only=True)
    name = StripTagsCharField(max_length=255)
    image = ValidImageField(required=False)
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)
    criteria = MarkdownCharField(allow_blank=True, required=False, write_only=True)
    criteria_text = MarkdownCharField(required=False, allow_null=True, allow_blank=True)
    criteria_url = StripTagsCharField(required=False, allow_blank=True, allow_null=True, validators=[URLValidator()])
    description = StripTagsCharField(max_length=16384, required=True, convert_null=True)
    alignment = AlignmentItemSerializerV1(many=True, source='alignment_items', required=False)
    tags = serializers.ListField(child=StripTagsCharField(max_length=1024), source='tag_items', required=False)
    extensions = serializers.DictField(source='extension_items', required=False)

    class Meta:
        apispec_definition = ('BadgeClass', {})

    def to_representation(self, instance):
        representation = super(BadgeClassSerializerV1, self).to_representation(instance)
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

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = BadgeClassExtension(name=extension_name,
                                            original_json=json.dumps(original_json),
                                            badgeclass_id=instance.pk)
            extension.save()

    def update(self, instance, validated_data):

        new_name = validated_data.get('name')
        if new_name:
            new_name = strip_tags(new_name)
            instance.name = new_name

        new_description = validated_data.get('description')
        if new_description:
            instance.description = strip_tags(new_description)

        if 'criteria_text' in validated_data:
            instance.criteria_text = validated_data.get('criteria_text')
        if 'criteria_url' in validated_data:
            instance.criteria_url = validated_data.get('criteria_url')

        if 'image' in validated_data:
            instance.image = validated_data.get('image')

        instance.alignment_items = validated_data.get('alignment_items')
        instance.tag_items = validated_data.get('tag_items')

        self.save_extensions(validated_data, instance)

        instance.save()

        return instance

    def validate(self, data):
        if 'criteria' in data:
            if 'criteria_url' in data or 'criteria_text' in data:
                raise serializers.ValidationError(
                    "The criteria field is mutually-exclusive with the criteria_url and criteria_text fields"
                )

            if utils.is_probable_url(data.get('criteria')):
                data['criteria_url'] = data.pop('criteria')
            elif not isinstance(data.get('criteria'), str):
                raise serializers.ValidationError(
                    "Provided criteria text could not be properly processed as URL or plain text."
                )
            else:
                data['criteria_text'] = data.pop('criteria')

        else:
            if data.get('criteria_text', None) is None and data.get('criteria_url', None) is None:
                raise serializers.ValidationError(
                    "One or both of the criteria_text and criteria_url fields must be provided"
                )

        return data

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['issuer'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            new_badgeclass = BadgeClass.objects.create(**validated_data)
            return new_badgeclass
        else:
            raise BadgrValidationError(fields="You don't have the necessary permissions")


class BadgeInstanceSerializerV1(OriginalJsonSerializerMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1(read_only=True)
    slug = serializers.CharField(max_length=255, read_only=True, source='entity_id')
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
    enrollment_slug = serializers.CharField(max_length=1024, required=False)

    create_notification = HumanReadableBooleanField(write_only=True, required=False, default=False)

    hashed = serializers.NullBooleanField(default=None, required=False)
    extensions = serializers.DictField(source='extension_items', required=False)

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

        representation = super(BadgeInstanceSerializerV1, self).to_representation(instance)
        representation['json'] = instance.get_json(obi_version="1_1", use_canonical_id=True)
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializerV1(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = OriginSetting.HTTP + reverse('issuer_json', kwargs={
                'entity_id': instance.cached_issuer.entity_id})
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializerV1(instance.cached_badgeclass,
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
        # ob2 evidence items
        if self.context['request'].data.get('issue_signed', False):
            assertion = self.context.get('badgeclass').issue_signed(
                recipient_id=validated_data.get('recipient_identifier'),
                created_by=self.context.get('request').user,
                allow_uppercase=validated_data.get('allow_uppercase'),
                recipient_type=validated_data.get('recipient_type', BadgeInstance.RECIPIENT_TYPE_EDUID),
                badgr_app=BadgrApp.objects.get_current(self.context.get('request')),
                expires_at=validated_data.get('expires_at', None),
                extensions=validated_data.get('extension_items', None),
                identifier=uuid.uuid4().urn,
                signer=validated_data.get('created_by'),
            )
        else:
            assertion = self.context.get('badgeclass').issue(
                recipient_id=validated_data.get('recipient_identifier'),
                notify=validated_data.get('create_notification'),
                created_by=self.context.get('request').user,
                allow_uppercase=validated_data.get('allow_uppercase'),
                recipient_type=validated_data.get('recipient_type', BadgeInstance.RECIPIENT_TYPE_EDUID),
                badgr_app=BadgrApp.objects.get_current(self.context.get('request')),
                expires_at=validated_data.get('expires_at', None),
                extensions=validated_data.get('extension_items', None)
            )

        related_enrollment = StudentsEnrolled.objects.get(entity_id=validated_data.get('enrollment_slug'))
        related_enrollment.date_awarded = timezone.now()
        related_enrollment.badge_instance = assertion
        related_enrollment.save()

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
