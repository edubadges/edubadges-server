import json
import os
import uuid
import datetime
from collections import OrderedDict
from itertools import chain

from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, EmailValidator
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from badgeuser.serializers import BadgeUserIdentifierField
from institution.serializers import FacultySlugRelatedField
from lti_edu.models import StudentsEnrolled
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError, BadgrValidationFieldError
from mainsite.models import BadgrApp
from mainsite.mixins import InternalValueErrorOverrideMixin
from mainsite.serializers import StripTagsCharField, MarkdownCharField, OriginalJsonSerializerMixin, BaseSlugRelatedField
from mainsite.utils import OriginSetting, scrub_svg_image, resize_image, verify_svg
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


class IssuerSerializer(OriginalJsonSerializerMixin, ExtensionsSaverMixin,
                       InternalValueErrorOverrideMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name_english = StripTagsCharField(max_length=1024, required=False, allow_null=True, allow_blank=True)
    name_dutch = StripTagsCharField(max_length=1024, required=False, allow_null=True, allow_blank=True)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    image_english = ValidImageField(required=False)
    image_dutch = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description_english = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    description_dutch = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)
    url_english = serializers.URLField(max_length=1024, required=False, allow_null=True, allow_blank=True)
    url_dutch = serializers.URLField(max_length=1024, required=False, allow_null=True, allow_blank=True)
    faculty = FacultySlugRelatedField(slug_field='entity_id', required=True)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    def _validate_image(self, image):
        img_name, img_ext = os.path.splitext(image.name)
        image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        image = resize_image(image)
        if verify_svg(image):
            image = scrub_svg_image(image)
        return image

    def validate_image_english(self, image_english):
        if image_english is not None:
            image_english = self._validate_image(image_english)
        return image_english

    def validate_image_dutch(self, image_dutch):
        if image_dutch is not None:
            image_dutch = self._validate_image(image_dutch)
        return image_dutch

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
        if instance.assertions and instance.name_english != validated_data["name_english"]:
            raise BadgrValidationError("Cannot change the name, assertions have already been issued within this entity", 214)
        if instance.assertions and instance.name_dutch != validated_data["name_dutch"]:
            raise BadgrValidationError("Cannot change the name, assertions have already been issued within this entity", 214)
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
        if not representation['image_english']:
            representation['image_english'] = obj.institution.image_url()
        if not representation['image_dutch']:
            representation['image_dutch'] = obj.institution.image_url()
        return representation

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        if data.get('email', False):
            try:
                EmailValidator().__call__(data.get('email'))
            except ValidationError:
                e = OrderedDict([('email', [ErrorDetail('Enter a valid email address.', code=509)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('name_english', False) and not data.get('name_dutch', False):
            e = OrderedDict([('name_english', [ErrorDetail('Either Dutch or English name is required', code=912)]),
                             ('name_dutch', [ErrorDetail('Either Dutch or English name is required', code=912)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('description_english', False) and not data.get('description_dutch', False):
            e = OrderedDict([('description_english', [ErrorDetail('Either Dutch or English description is required', code=913)]),
                             ('description_dutch', [ErrorDetail('Either Dutch or English description is required', code=913)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('url_english', False) and not data.get('url_dutch', False):
            e = OrderedDict([('url_english', [ErrorDetail('Either Dutch or English url is required', code=915)]),
                             ('url_dutch', [ErrorDetail('Either Dutch or English url is required', code=915)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors

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


class BadgeClassSerializer(OriginalJsonSerializerMixin, ExtensionsSaverMixin,
                           InternalValueErrorOverrideMixin, serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name = StripTagsCharField(max_length=255)
    image = ValidImageField(required=True)
    formal = serializers.BooleanField(required=True)
    is_private = serializers.BooleanField(required=False, default=False)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)
    criteria = MarkdownCharField(allow_blank=True, required=False, write_only=True)
    criteria_text = MarkdownCharField(required=False, allow_null=True, allow_blank=True)
    criteria_url = StripTagsCharField(required=False, allow_blank=True, allow_null=True, validators=[URLValidator()])
    description = StripTagsCharField(max_length=16384, required=True, convert_null=True)
    alignments = AlignmentItemSerializer(many=True, source='alignment_items', required=False)
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
            image = resize_image(image)
            if verify_svg(image):
                image = scrub_svg_image(image)
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

    def validate_extensions(self, extensions):
        if extensions:
            for ext in extensions.values():
                if "@context" in ext and not ext['@context'].startswith(settings.EXTENSIONS_ROOT_URL):
                    raise BadgrValidationError(
                        error_code=999,
                        error_message=f"extensions @context invalid {ext['@context']}")
        return extensions

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
                error_code=999,
                error_message="Cannot change any value, assertions have already been issued")
        self.save_extensions(validated_data, instance)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        try:
            instance.save()
        except IntegrityError:
            raise BadgrValidationFieldError('name',
                                            "There is already a Badgeclass with this name inside this Issuer",
                                            911)
        return instance

    def validate_alignments(self, alignments):
        alignment_max = 8
        if alignments.__len__() >= alignment_max:
            raise BadgrValidationFieldError('alignments',
                                            "There are too many Related educational framework objects, the maximum is {}.".format(str(alignment_max),
                                            921)
            )
        return alignments

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer excpetions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        if not data.get('criteria_text', False) and not data.get('criteria_url', False):
            e = OrderedDict([('criteria_text', [ErrorDetail('Either criteria_url or criteria_text is required', code=905)]),
                             ('criteria_url', [ErrorDetail('Either criteria_url or criteria_text is required', code=905)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if data.get('criteria_url', False):
            if not utils.is_probable_url(data.get('criteria_url')):
                e = OrderedDict([('criteria_url', [ErrorDetail('Must be a proper url.', code=902)])])
                errors = OrderedDict(chain(errors.items(), e.items()))
        if data.get('name') == settings.EDUID_BADGE_CLASS_NAME:
            e = OrderedDict([('name', [ErrorDetail(f"{settings.EDUID_BADGE_CLASS_NAME} is a reserved name for badgeclasses",
                                                   code=907)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['issuer'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            if validated_data['formal'] and not validated_data['issuer'].faculty.institution.grondslag_formeel:
                raise BadgrValidationError("Cannot create a formal badgeclass for an institution without the judicial basis for formal badges", 215)
            if not validated_data['formal'] and not validated_data['issuer'].faculty.institution.grondslag_informeel:
                raise BadgrValidationError("Cannot create an informal badgeclass for an institution without the judicial basis for informal badges", 216)
            try:
                new_badgeclass = BadgeClass.objects.create(**validated_data)
            except IntegrityError:
                raise BadgrValidationFieldError('name',
                                                "There is already a Badgeclass with this name inside this Issuer",
                                                911)
            return new_badgeclass
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)


class EvidenceItemSerializer(serializers.Serializer):
    evidence_url = serializers.URLField(max_length=1024, required=False, allow_blank=True)
    narrative = MarkdownCharField(required=False, allow_blank=True)

    def validate(self, attrs):
        if not (attrs.get('evidence_url', None) or attrs.get('narrative', None)):
            raise BadgrValidationFieldError('narrative',
                                            "Either url or narrative is required",
                                            910)
        return attrs


class BadgeInstanceSerializer(OriginalJsonSerializerMixin, serializers.Serializer):
    allow_uppercase = serializers.BooleanField(default=False, required=False, write_only=True)
    issue_signed = serializers.BooleanField(required=False)
    signing_password = serializers.CharField(max_length=1024, required=False)
    enrollment_entity_id = serializers.CharField(max_length=1024, required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])

    narrative = MarkdownCharField(required=False, allow_blank=True, allow_null=True)
    evidence_items = EvidenceItemSerializer(many=True, required=False)

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
                expires_at=expires_at,
                extensions=validated_data.get('extension_items', None),
                identifier=uuid.uuid4().urn,
                signer=validated_data.get('created_by'),
                # evidence=validated_data.get('evidence_items', None)  # Dont forget this one when you re-implement signing
                # narrative=validated_data.get('narrative', None)  # idem
            )
        else:
            assertion = badgeclass.issue(
                recipient=enrollment.user,
                created_by=self.context.get('request').user,
                allow_uppercase=validated_data.get('allow_uppercase'),
                recipient_type=validated_data.get('recipient_type', BadgeInstance.RECIPIENT_TYPE_EDUID),
                expires_at=expires_at,
                extensions=validated_data.get('extension_items', None),
                evidence=validated_data.get('evidence_items', None),
                narrative=validated_data.get('narrative', None)
            )

        enrollment.date_awarded = timezone.now()
        enrollment.badge_instance = assertion
        enrollment.save()
        enrollment.user.remove_cached_data(['cached_pending_enrollments'])
        return assertion
