import datetime
import json
import os
import uuid
from collections import OrderedDict
from itertools import chain

import badgrlog
from badgeuser.serializers import BadgeUserIdentifierField
from django.apps import apps
from django.conf import settings
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from institution.models import BadgeClassTag, Institution
from institution.serializers import FacultySlugRelatedField
from lti_edu.models import StudentsEnrolled
from mainsite.drf_fields import ValidImageField
from mainsite.exceptions import BadgrValidationError, BadgrValidationFieldError
from mainsite.mixins import InternalValueErrorOverrideMixin
from mainsite.models import BadgrApp
from mainsite.serializers import (
    BaseSlugRelatedField,
    MarkdownCharField,
    OriginalJsonSerializerMixin,
    StripTagsCharField,
)
from mainsite.settings import EWI_PILOT_EXPIRATION_DATE
from mainsite.utils import OriginSetting, add_watermark, resize_image, scrub_svg_image, verify_svg
from mainsite.validators import BadgeExtensionValidator
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail, ValidationError
from rest_framework.serializers import PrimaryKeyRelatedField

from .models import BadgeClass, BadgeClassExtension, BadgeInstance, BadgeInstanceCollection, Issuer, IssuerExtension


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


class IssuerSerializer(
    OriginalJsonSerializerMixin, ExtensionsSaverMixin, InternalValueErrorOverrideMixin, serializers.Serializer
):
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
        app = BadgrApp.objects.get_current(self.context.get('request', None))
        is_svg = verify_svg(image)
        if is_svg:
            image = scrub_svg_image(image)
        if app.is_demo_environment:
            image = add_watermark(image, is_svg)
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
            representation['badgeclasses'] = BadgeClassSerializer(
                obj.badgeclasses.all(), many=True, context=self.context
            ).data
        if not representation['image_english']:
            representation['image_english'] = obj.institution.image_url()
        if not representation['image_dutch']:
            representation['image_dutch'] = obj.institution.image_url()
        return representation

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions
        before the instance is saved (i.e. the save() method is called)"""
        errors = OrderedDict()
        if not data.get('name_dutch', False) and not data.get('name_english', False):
            e = OrderedDict([('name_dutch', [ErrorDetail('Dutch or English name is required', code=912)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict([('name_english', [ErrorDetail('English or Dutch name is required', code=924)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('description_dutch', False) and not data.get('description_english', False):
            e = OrderedDict(
                [('description_dutch', [ErrorDetail('Dutch or English description is required', code=913)])]
            )
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict(
                [('description_english', [ErrorDetail('English or Dutch description is required', code=925)])]
            )
            errors = OrderedDict(chain(errors.items(), e.items()))
        if not data.get('url_dutch', False) and not data.get('url_english', False):
            e = OrderedDict([('url_dutch', [ErrorDetail('Dutch or English url is required', code=915)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
            e = OrderedDict([('url_english', [ErrorDetail('English or Dutch url is required', code=923)])])
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = IssuerExtension(
                name=extension_name, original_json=json.dumps(original_json), issuer_id=instance.pk
            )
            extension.save()


class AlignmentItemSerializer(serializers.Serializer):
    target_name = StripTagsCharField()
    target_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    target_description = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_framework = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    target_code = StripTagsCharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        apispec_definition = ('BadgeClassAlignment', {})

    def validate_target_url(self, target_url):
        if not self.root.initial_data.get('isMicroCredentials', True):
            if not target_url or len(target_url.strip()) == 0:
                raise ValidationError(detail='This field may not be blank.', code='blank')
        return target_url


class BadgeClassSerializer(
    OriginalJsonSerializerMixin, ExtensionsSaverMixin, InternalValueErrorOverrideMixin, serializers.Serializer
):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name = StripTagsCharField(max_length=255)
    image = ValidImageField(required=False, allow_empty_file=True)
    formal = serializers.BooleanField(required=True)
    is_private = serializers.BooleanField(required=False, default=False)
    narrative_required = serializers.BooleanField(required=False, default=False)
    evidence_required = serializers.BooleanField(required=False, default=False)
    narrative_student_required = serializers.BooleanField(required=False, default=False)
    evidence_student_required = serializers.BooleanField(required=False, default=False)
    award_non_validated_name_allowed = serializers.BooleanField(required=False, default=False)
    is_micro_credentials = serializers.BooleanField(required=False, default=False)
    direct_awarding_disabled = serializers.BooleanField(required=False, default=False)
    self_enrollment_disabled = serializers.BooleanField(required=False, default=False)
    entity_id = StripTagsCharField(max_length=255, read_only=True)
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)
    criteria_text = MarkdownCharField(required=False, allow_null=True, allow_blank=True)
    description = StripTagsCharField(max_length=16384, required=False, convert_null=True, allow_blank=True)
    badge_class_type = StripTagsCharField(required=True, allow_blank=False, allow_null=False)
    participation = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    assessment_type = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    assessment_id_verified = serializers.BooleanField(required=False, default=False)
    assessment_supervised = serializers.BooleanField(required=False, default=False)
    quality_assurance_name = StripTagsCharField(required=False, allow_blank=True, allow_null=True)
    quality_assurance_url = StripTagsCharField(
        required=False, allow_blank=True, allow_null=True, validators=[URLValidator()]
    )
    quality_assurance_description = MarkdownCharField(required=False, allow_blank=True, allow_null=True)
    grade_achieved_required = serializers.BooleanField(required=False, default=False)
    eqf_nlqf_level_verified = serializers.BooleanField(required=False, default=False)
    stackable = serializers.BooleanField(required=False, default=False)

    alignments = AlignmentItemSerializer(many=True, source='alignment_items', required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])
    expiration_period = PeriodField(required=False)
    award_allowed_institutions = PrimaryKeyRelatedField(many=True, queryset=Institution.objects.all(), required=False)
    tags = PrimaryKeyRelatedField(many=True, queryset=BadgeClassTag.objects.all(), required=False)

    def validate(self, data):
        """
        For each type of badge there are different required fields
        """
        issuer = data['issuer']
        required_fields = ['name']
        extensions = ['LanguageExtension']
        is_mbo = issuer.institution.institution_type == Institution.TYPE_MBO
        is_private = data.get('is_private', False)
        type_badge = data['badge_class_type']
        self.formal = type_badge == BadgeClass.BADGE_CLASS_TYPE_REGULAR
        if is_mbo and not is_private and type_badge != BadgeClass.BADGE_CLASS_TYPE_CURRICULAR:
            extensions += ['StudyLoadExtension']
        if not is_private:
            required_fields += ['description', 'criteria_text']
            if type_badge == BadgeClass.BADGE_CLASS_TYPE_MICRO:
                required_fields += [
                    'participation',
                    'assessment_type',
                    'quality_assurance_name',
                    'quality_assurance_url',
                    'quality_assurance_description',
                ]
                extensions += ['LearningOutcomeExtension', 'EQFExtension']
            elif type_badge == BadgeClass.BADGE_CLASS_TYPE_REGULAR:
                required_fields += ['criteria_text']
                extensions += ['LearningOutcomeExtension', 'EQFExtension', 'EducationProgramIdentifierExtension']

        errors = OrderedDict()
        for field_name in required_fields:
            if data.get(field_name) is None:
                errors[field_name] = ErrorDetail('This field may not be blank.', code='blank')
        extension_items = data.get('extension_items', [])
        for extension in extensions:
            if not extension_items.get(f'extensions:{extension}'):
                errors[f'extensions.{extension}'] = ErrorDetail('This field may not be blank.', code='blank')
        if errors:
            raise ValidationError(errors)

        return data

    class Meta:
        apispec_definition = ('BadgeClass', {})
        model = BadgeClass

    def get_expiration_period(self, instance):
        if instance.expiration_period:
            return instance.expiration_period.days

    def to_representation(self, instance):
        representation = super(BadgeClassSerializer, self).to_representation(instance)
        representation['issuer'] = OriginSetting.HTTP + reverse(
            'issuer_json', kwargs={'entity_id': instance.cached_issuer.entity_id}
        )
        representation['json'] = instance.get_json(obi_version='1_1', use_canonical_id=True)
        return representation

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_badgeclass_' + str(uuid.uuid4()) + img_ext
            image = resize_image(image)
            is_svg = verify_svg(image)
            if is_svg:
                image = scrub_svg_image(image)
            image = add_watermark(image, is_svg)
        return image

    def validate_criteria_text(self, criteria_text):
        if criteria_text is not None and criteria_text != '':
            return criteria_text
        else:
            return None

    def validate_name(self, name):
        return strip_tags(name)

    def validate_description(self, description):
        return strip_tags(description)

    def validate_extensions(self, extensions):
        if extensions:
            for ext_name, ext in extensions.items():
                if '@context' in ext and not ext['@context'].startswith(settings.EXTENSIONS_ROOT_URL):
                    raise BadgrValidationError(
                        error_code=999, error_message=f'extensions @context invalid {ext["@context"]}'
                    )
        return extensions

    def add_extensions(self, instance, add_these_extensions, extension_items):
        for extension_name in add_these_extensions:
            original_json = extension_items[extension_name]
            extension = BadgeClassExtension(
                name=extension_name, original_json=json.dumps(original_json), badgeclass_id=instance.pk
            )
            extension.save()

    def update(self, instance, validated_data):
        has_unrevoked_assertions = (
            instance.assertions and len([ass for ass in instance.assertions if not ass.revoked]) > 0
        )
        if not has_unrevoked_assertions:
            self.save_extensions(validated_data, instance)
        allowed_keys = [
            'narrative_required',
            'evidence_required',
            'narrative_student_required',
            'evidence_student_required',
            'award_non_validated_name_allowed',
            'direct_awarding_disabled',
            'self_enrollment_disabled',
            'alignment_items',
            'expiration_period',
            'self_enrollment_disabled',
            'stackable',
            'grade_achieved_required',
            'eqf_nlqf_level_verified',
        ]
        # Because of new required fields there are invalid badge_classes that are allowed to update
        upgrade_keys = [
            'quality_assurance_description',
            'quality_assurance_name',
            'quality_assurance_url',
            'assessment_type',
            'assessment_supervised',
            'assessment_id_verified',
            'participation',
        ]
        many_to_many_keys = ['award_allowed_institutions', 'tags']
        for key, value in validated_data.items():
            if key not in many_to_many_keys and (not has_unrevoked_assertions or key in allowed_keys):
                setattr(instance, key, value)
            if key in upgrade_keys and getattr(instance, key) is None:
                setattr(instance, key, value)
            if key == 'extension_items':
                has_existing_lo = [
                    ext
                    for ext in list(instance.badgeclassextension_set.all())
                    if ext.name == 'extensions:LearningOutcomeExtension'
                ]
                has_new_lo = validated_data.get('extension_items').get('extensions:LearningOutcomeExtension', False)
                # Corner case where previously LO was not required and now is
                if not has_existing_lo and has_new_lo:
                    setattr(instance, key, value)
        instance.award_allowed_institutions.set(validated_data.get('award_allowed_institutions', []))
        instance.tags.set(validated_data.get('tags', []))
        badge_class = BadgeClass.objects.get(id=instance.id)
        if badge_class.issuer.id != validated_data['issuer'].id:
            badge_class.issuer.faculty.remove_cached_data(['cached_badgeclasses'])
            badge_class.issuer.remove_cached_data(['cached_badgeclasses'])
        instance.save()
        return instance

    def validate_alignments(self, alignments):
        alignment_max = 8
        if alignments.__len__() >= alignment_max:
            raise BadgrValidationFieldError(
                'alignments',
                'There are too many Related educational framework objects, the maximum is {}.'.format(
                    str(alignment_max),
                ),
            )
        return alignments

    def to_internal_value_error_override(self, data):
        """Function used in combination with the InternalValueErrorOverrideMixin to override serializer exceptions when
        data is internalised (i.e. the to_internal_value() method is called)"""
        errors = OrderedDict()
        if data.get('name') == settings.EDUID_BADGE_CLASS_NAME:
            e = OrderedDict(
                [
                    (
                        'name',
                        [
                            ErrorDetail(
                                f'{settings.EDUID_BADGE_CLASS_NAME} is a reserved name for badgeclasses', code=907
                            )
                        ],
                    )
                ]
            )
            errors = OrderedDict(chain(errors.items(), e.items()))
        return errors

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['issuer'].get_permissions(validated_data['created_by'])
        if user_permissions['may_create']:
            is_micro_micro_credential = validated_data['badge_class_type'] == 'micro_credential'
            institution = validated_data['issuer'].faculty.institution
            if is_micro_micro_credential and not institution.micro_credentials_enabled:
                raise BadgrValidationError(
                    'Cannot create a micro_credential badgeclass for an institution not configured for ', 217
                )
            if validated_data['formal'] and not institution.grondslag_formeel and not is_micro_micro_credential:
                raise BadgrValidationError(
                    'Cannot create a formal badgeclass for an institution without the judicial basis for formal badges',
                    215,
                )
            if not validated_data['formal'] and not institution.grondslag_informeel and not is_micro_micro_credential:
                raise BadgrValidationError(
                    'Cannot create an informal badgeclass for an institution without the judicial basis for informal badges',
                    216,
                )
            tags = validated_data.get('tags', [])
            if 'tags' in validated_data:
                del validated_data['tags']
            new_badgeclass = BadgeClass.objects.create(**validated_data)
            new_badgeclass.tags.set(tags)
            new_badgeclass.save()

            logger = badgrlog.BadgrLogger()
            logger.event(badgrlog.BadgeClassCreatedEvent(new_badgeclass))

            return new_badgeclass
        else:
            raise BadgrValidationError("You don't have the necessary permissions", 100)


class EvidenceItemSerializer(serializers.Serializer):
    evidence_url = serializers.URLField(max_length=1024, required=False, allow_null=True, allow_blank=True)
    narrative = MarkdownCharField(required=False, allow_blank=True, allow_null=True)
    name = serializers.CharField(max_length=255, required=False, allow_null=True, allow_blank=True)
    description = StripTagsCharField(max_length=16384, required=False, allow_null=True, allow_blank=True)

    def validate(self, attrs):
        if not (attrs.get('evidence_url', None) or attrs.get('narrative', None)):
            raise BadgrValidationFieldError('narrative', 'Either url or narrative is required', 910)
        return attrs


class BadgeInstanceSerializer(OriginalJsonSerializerMixin, serializers.Serializer):
    allow_uppercase = serializers.BooleanField(default=False, required=False, write_only=True)
    issue_signed = serializers.BooleanField(required=False)
    signing_password = serializers.CharField(max_length=1024, required=False)
    enrollment_entity_id = serializers.CharField(max_length=1024, required=False)
    extensions = serializers.DictField(source='extension_items', required=False, validators=[BadgeExtensionValidator()])
    grade_achieved = serializers.CharField(max_length=254, required=False, allow_blank=True, allow_null=True)
    narrative = MarkdownCharField(required=False, allow_blank=True, allow_null=True)
    evidence_items = EvidenceItemSerializer(many=True, required=False)

    def get_recipient_email(self, obj):
        return obj.get_email_address()

    def get_recipient_name(self, obj):
        return obj.get_recipient_name()

    def validate(self, data):
        badgeclass = self.context['request'].data.get('badgeclass')
        if badgeclass.narrative_required and not data.get('narrative'):
            raise BadgrValidationError(error_code=999, error_message='Narrative is required')
        if badgeclass.evidence_required and not data.get('evidence_items'):
            raise BadgrValidationError(error_code=999, error_message='Evidence is required')
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
        if data is None or data == '':
            return None
        else:
            return data

    def to_representation(self, instance):
        representation = super(BadgeInstanceSerializer, self).to_representation(instance)
        representation['json'] = instance.get_json(obi_version='1_1', use_canonical_id=True)
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializer(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = OriginSetting.HTTP + reverse(
                'issuer_json', kwargs={'entity_id': instance.cached_issuer.entity_id}
            )
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializer(instance.cached_badgeclass, context=self.context).data
        else:
            representation['badge_class'] = OriginSetting.HTTP + reverse(
                'badgeclass_json', kwargs={'entity_id': instance.cached_badgeclass.entity_id}
            )

        representation['public_url'] = OriginSetting.HTTP + reverse(
            'badgeinstance_json', kwargs={'entity_id': instance.entity_id}
        )

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
        da = badgeclass.cached_pending_direct_awards().filter(eppn__in=enrollment.user.eppns)

        max_expiration = EWI_PILOT_EXPIRATION_DATE
        if badgeclass.expiration_period:
            badge_expiration = (
                timezone.now().replace(microsecond=0, second=0, minute=0, hour=0) + badgeclass.expiration_period
            )
            expires_at = min(badge_expiration, max_expiration)
        else:
            expires_at = max_expiration

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
                issued_on=enrollment.date_created,
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
                narrative=validated_data.get('narrative', None),
                grade_achieved=validated_data.get('grade_achieved', None),
                issued_on=enrollment.date_created,
            )

        enrollment.date_awarded = timezone.now()
        enrollment.badge_instance = assertion
        enrollment.deny_reason = None
        enrollment.denied = False
        enrollment.save()
        enrollment.user.remove_cached_data(['cached_pending_enrollments'])
        # delete the pending direct awards for this badgeclass and this user
        badgeclass.cached_pending_direct_awards().filter(eppn__in=enrollment.user.eppns).delete()

        # Log the badge instance creation event
        logger = badgrlog.BadgrLogger()
        logger.event(badgrlog.BadgeInstanceCreatedEvent(assertion))

        return assertion


class BadgeInstanceCollectionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=254)
    description = serializers.CharField(max_length=256, required=False, allow_null=True, allow_blank=True)
    badge_instances = PrimaryKeyRelatedField(many=True, queryset=BadgeInstance.objects.all(), required=False)

    class Meta:
        model = BadgeInstanceCollection

    def create(self, validated_data):
        instance = BadgeInstanceCollection.objects.create(
            name=validated_data['name'],
            description=validated_data.get('description'),
        )
        instance.user = self.context['request'].user
        instance.badge_instances.set(validated_data.get('badge_instances', []))
        instance.save()
        return instance

    def update(self, instance, validated_data):
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data if attr != 'badge_instances']
        instance.save()
        instance.badge_instances.set(validated_data.get('badge_instances', []))
        return instance

    def validate_badge_instances(self, badge_instances):
        user = self.context['request'].user
        for bc in badge_instances:
            if bc.user != user:
                raise IntegrityError('BadgeInstance must be owned by the current user.')
        return badge_instances
