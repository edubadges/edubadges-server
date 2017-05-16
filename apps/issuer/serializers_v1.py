import uuid

import os
from django.apps import apps
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from rest_framework import serializers
from rest_framework.compat import URLValidator

import utils
from badgeuser.serializers_v1 import BadgeUserProfileSerializerV1, BadgeUserIdentifierFieldV1
from mainsite.drf_fields import ValidImageField
from mainsite.models import BadgrApp
from mainsite.serializers import HumanReadableBooleanField, StripTagsCharField, MarkdownCharField
from mainsite.utils import OriginSetting
from mainsite.validators import ChoicesValidator
from .models import Issuer, BadgeClass, IssuerStaff


class CachedListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return [self.child.to_representation(item) for item in data]


class IssuerStaffSerializerV1(serializers.Serializer):
    """ A read_only serializer for staff roles """
    user = BadgeUserProfileSerializerV1(source='cached_user')
    role = serializers.CharField(validators=[ChoicesValidator(dict(IssuerStaff.ROLE_CHOICES).keys())])

    class Meta:
        list_serializer_class = CachedListSerializer

        apispec_definition = ('IssuerStaff', {
            'properties': {
                'role': {
                    'type': "string",
                    'enum': ["staff", "editor", "owner"]

                }
            }
        })


class IssuerSerializerV1(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1()
    name = StripTagsCharField(max_length=1024)
    slug = StripTagsCharField(max_length=255, source='entity_id', read_only=True)
    image = ValidImageField(required=False)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=1024, required=True)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializerV1(read_only=True, source='cached_issuerstaff', many=True)

    class Meta:
        apispec_definition = ('Issuer', {})

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data, **kwargs):
        new_issuer = Issuer(**validated_data)
        new_issuer.save()
        return new_issuer

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')

        if 'image' in validated_data:
            instance.image = validated_data.get('image')

        instance.email = validated_data.get('email')
        instance.description = validated_data.get('description')
        instance.url = validated_data.get('url')

        instance.save()
        return instance

    def to_representation(self, obj):
        representation = super(IssuerSerializerV1, self).to_representation(obj)
        representation['json'] = obj.get_json()

        if self.context.get('embed_badgeclasses', False):
            representation['badgeclasses'] = BadgeClassSerializerV1(obj.badgeclasses.all(), many=True, context=self.context).data

        representation['badgeClassCount'] = len(obj.cached_badgeclasses())
        representation['recipientGroupCount'] = len(obj.cached_recipient_groups())
        representation['recipientCount'] = sum(g.member_count() for g in obj.cached_recipient_groups())
        representation['pathwayCount'] = len(obj.cached_pathways())

        return representation


class IssuerRoleActionSerializerV1(serializers.Serializer):
    """ A serializer used for validating user role change POSTS """
    action = serializers.ChoiceField(('add', 'modify', 'remove'), allow_blank=True)
    username = serializers.CharField(allow_blank=True, required=False)
    email = serializers.EmailField(allow_blank=True, required=False)
    editor = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if attrs.get('username') and attrs.get('email'):
            raise serializers.ValidationError(
                'Either a username or email address must be provided, not both.')
        return attrs


class BadgeClassSerializerV1(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1()
    id = serializers.IntegerField(required=False, read_only=True)
    name = StripTagsCharField(max_length=255)
    image = ValidImageField(required=False)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')
    criteria = MarkdownCharField(allow_blank=True, required=False, write_only=True)
    criteria_text = MarkdownCharField(required=False, allow_null=True)
    criteria_url = StripTagsCharField(required=False, validators=[URLValidator()])
    recipient_count = serializers.IntegerField(required=False, read_only=True)
    pathway_element_count = serializers.IntegerField(required=False, read_only=True)
    description = StripTagsCharField(max_length=16384, required=True)

    def to_representation(self, instance):
        representation = super(BadgeClassSerializerV1, self).to_representation(instance)
        representation['issuer'] = OriginSetting.HTTP+reverse('issuer_json', kwargs={'entity_id': instance.cached_issuer.entity_id})
        representation['json'] = instance.get_json()
        return representation

    def validate_image(self, image):
        if image is not None:
            img_name, img_ext = os.path.splitext(image.name)
            image.name = 'issuer_badgeclass_' + str(uuid.uuid4()) + img_ext
        return image

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

        instance.save()
        return instance

    def validate(self, data):

        if 'criteria' in data:
            if utils.is_probable_url(data.get('criteria')):
                data['criteria_url'] = data.pop('criteria')
            elif not isinstance(data.get('criteria'), (str, unicode)):
                raise serializers.ValidationError(
                    "Provided criteria text could not be properly processed as URL or plain text."
                )
            else:
                data['criteria_text'] = data.pop('criteria')

        return data

    def create(self, validated_data, **kwargs):

        if 'image' not in validated_data:
            raise serializers.ValidationError({"image": ["This field is required"]})

        if 'issuer' in self.context:
            validated_data['issuer'] = self.context.get('issuer')

        new_badgeclass = BadgeClass(**validated_data)

        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_badgeclass.slug = BadgeClass._meta.get_field('slug').pre_save(new_badgeclass, add=True)

        new_badgeclass.save()
        return new_badgeclass


class EvidenceItemSerializer(serializers.Serializer):
    evidence_url = serializers.URLField(max_length=1024, required=False)
    narrative = MarkdownCharField(required=False)

    def validate(self, attrs):
        if not (attrs.get('evidence_url', None) or attrs.get('narrative', None)):
            raise serializers.ValidationError("Either url or narrative is required")
        return attrs


class BadgeInstanceSerializerV1(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierFieldV1()
    slug = serializers.CharField(max_length=255, read_only=True, source='entity_id')
    image = serializers.FileField(read_only=True)  # use_url=True, might be necessary
    email = serializers.EmailField(max_length=1024, required=False, write_only=True)
    recipient_identifier = serializers.EmailField(max_length=1024, required=False)
    allow_uppercase = serializers.BooleanField(default=False, required=False, write_only=True)
    evidence = serializers.URLField(write_only=True, required=False, allow_blank=True, max_length=1024)
    narrative = MarkdownCharField(required=False)
    evidence_items = EvidenceItemSerializer(many=True, required=False)

    revoked = HumanReadableBooleanField(read_only=True)
    revocation_reason = serializers.CharField(read_only=True)

    create_notification = HumanReadableBooleanField(write_only=True, required=False, default=False)

    def validate(self, data):
        if data.get('email') and not data.get('recipient_identifier'):
            data['recipient_identifier'] = data.get('email')

        return data

    def to_representation(self, instance):
        # if self.context.get('extended_json'):
        #     self.fields['json'] = V1InstanceSerializer(source='extended_json')

        representation = super(BadgeInstanceSerializerV1, self).to_representation(instance)
        representation['json'] = instance.get_json()
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializerV1(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = OriginSetting.HTTP+reverse('issuer_json', kwargs={'entity_id': instance.cached_issuer.entity_id})
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializerV1(instance.cached_badgeclass, context=self.context).data
        else:
            representation['badge_class'] = OriginSetting.HTTP+reverse('badgeclass_json', kwargs={'entity_id': instance.cached_badgeclass.entity_id})

        representation['public_url'] = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={'entity_id': instance.entity_id})

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
        evidence_items = []

        # ob1 evidence url
        evidence_url = validated_data.get('evidence')
        if evidence_url:
            evidence_items.append({'evidence_url': evidence_url})

        # ob2 evidence items
        submitted_items = self.validated_data.get('evidence_items')
        if submitted_items:
            evidence_items.extend(submitted_items)

        return self.context.get('badgeclass').issue(
            recipient_id=validated_data.get('recipient_identifier'),
            evidence=evidence_items,
            notify=validated_data.get('create_notification'),
            created_by=self.context.get('request').user,
            allow_uppercase=validated_data.get('allow_uppercase'),
            badgr_app=BadgrApp.objects.get_current(self.context.get('request'))
        )
