import os
import uuid

from django.apps import apps
from django.core.urlresolvers import reverse
from django.utils.html import strip_tags
from rest_framework import serializers

import utils
from badgeuser.serializers import BadgeUserProfileSerializer, BadgeUserIdentifierField
from mainsite.drf_fields import Base64FileField
from mainsite.models import BadgrApp
from mainsite.serializers import HumanReadableBooleanField, StripTagsCharField
from mainsite.utils import installed_apps_list, OriginSetting, verify_svg
from .models import Issuer, BadgeClass, IssuerStaff


class CachedListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return [self.child.to_representation(item) for item in data]


class IssuerStaffSerializer(serializers.Serializer):
    """ A read_only serializer for staff roles """
    user = BadgeUserProfileSerializer(source='cached_user')
    role = serializers.CharField()

    class Meta:
        list_serializer_class = CachedListSerializer

    def validate_role(self, role):
        valid_roles = dict(IssuerStaff.ROLE_CHOICES).keys()
        role = role.lower()
        if role not in valid_roles:
            raise serializers.ValidationError("Invalid role. Available roles: {}".format(valid_roles))
        return role


class IssuerSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    name = StripTagsCharField(max_length=1024)
    slug = StripTagsCharField(max_length=255, allow_blank=True, required=False)
    image = Base64FileField(allow_empty_file=False, use_url=True, required=False, allow_null=True)
    email = serializers.EmailField(max_length=255, required=True)
    description = StripTagsCharField(max_length=1024, required=True)
    url = serializers.URLField(max_length=1024, required=True)
    staff = IssuerStaffSerializer(read_only=True, source='cached_staff_records', many=True)

    def validate(self, data):
        # TODO: ensure email is a confirmed email in owner/creator's account
        # ^^^ that validation requires the request.user, which might be in self.context
        return data

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        # Doing: add a random string to filename

        if image is None:
            return image

        img_name, img_ext = os.path.splitext(image.name)

        try:
            from PIL import Image
            img = Image.open(image)
            img.verify()
        except Exception as e:
            if not verify_svg(image):
                raise serializers.ValidationError('Invalid image.')
        else:
            if img.format != "PNG":
                raise serializers.ValidationError('Invalid PNG')

        image.name = 'issuer_logo_' + str(uuid.uuid4()) + img_ext
        return image

    def create(self, validated_data, **kwargs):
        new_issuer = Issuer(**validated_data)

        # TODO: Is this needed anymore? [Wiggins Feb 2017]
        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_issuer.slug = Issuer._meta.get_field('slug').pre_save(new_issuer, add=True)

        new_issuer.save()

        staff = IssuerStaff(issuer=new_issuer, user=new_issuer.created_by, role=IssuerStaff.ROLE_OWNER)
        staff.save()
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
        representation = super(IssuerSerializer, self).to_representation(obj)
        representation['json'] = obj.get_json()

        if self.context.get('embed_badgeclasses', False):
            representation['badgeclasses'] = BadgeClassSerializer(obj.badgeclasses.all(), many=True, context=self.context).data

        representation['badgeClassCount'] = len(obj.cached_badgeclasses())
        representation['recipientGroupCount'] = len(obj.cached_recipient_groups())
        representation['recipientCount'] = sum(g.member_count() for g in obj.cached_recipient_groups())
        representation['pathwayCount'] = len(obj.cached_pathways())

        return representation


class IssuerRoleActionSerializer(serializers.Serializer):
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


class BadgeClassSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    id = serializers.IntegerField(required=False, read_only=True)
    name = StripTagsCharField(max_length=255)
    image = Base64FileField(allow_empty_file=False, use_url=True, required=False)
    slug = StripTagsCharField(max_length=255, allow_blank=True, required=False)
    criteria = StripTagsCharField(allow_blank=True, required=False, write_only=True)
    criteria_text = StripTagsCharField(required=False, read_only=True)
    criteria_url = StripTagsCharField(required=False, read_only=True)
    recipient_count = serializers.IntegerField(required=False, read_only=True)
    pathway_element_count = serializers.IntegerField(required=False, read_only=True)
    description = StripTagsCharField(max_length=16384, required=True)

    def to_representation(self, instance):
        representation = super(BadgeClassSerializer, self).to_representation(instance)
        representation['issuer'] = OriginSetting.HTTP+reverse('issuer_json', kwargs={'slug': instance.cached_issuer.slug})
        representation['json'] = instance.get_json()
        return representation

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        # Doing: add a random string to filename
        img_name, img_ext = os.path.splitext(image.name)

        try:
            from PIL import Image
            img = Image.open(image)
            img.verify()
        except Exception as e:
            if not verify_svg(image):
                raise serializers.ValidationError('Invalid image.')
        else:
            if img.format != "PNG":
                raise serializers.ValidationError('Invalid PNG')

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

        new_badgeclass = BadgeClass(**validated_data)

        # Use AutoSlugField's pre_save to provide slug if empty, else auto-unique
        new_badgeclass.slug = BadgeClass._meta.get_field('slug').pre_save(new_badgeclass, add=True)

        new_badgeclass.save()
        return new_badgeclass


class BadgeInstanceSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = BadgeUserIdentifierField()
    slug = serializers.CharField(max_length=255, read_only=True)
    image = serializers.FileField(read_only=True)  # use_url=True, might be necessary
    email = serializers.EmailField(max_length=1024, required=False, write_only=True)
    recipient_identifier = serializers.EmailField(max_length=1024, required=False)
    allow_uppercase = serializers.BooleanField(default=False, required=False, write_only=True)
    evidence = serializers.URLField(write_only=True, required=False, allow_blank=True, max_length=1024)

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

        representation = super(BadgeInstanceSerializer, self).to_representation(instance)
        representation['json'] = instance.get_json()
        if self.context.get('include_issuer', False):
            representation['issuer'] = IssuerSerializer(instance.cached_badgeclass.cached_issuer).data
        else:
            representation['issuer'] = OriginSetting.HTTP+reverse('issuer_json', kwargs={'slug': instance.cached_issuer.slug})
        if self.context.get('include_badge_class', False):
            representation['badge_class'] = BadgeClassSerializer(instance.cached_badgeclass, context=self.context).data
        else:
            representation['badge_class'] = OriginSetting.HTTP+reverse('badgeclass_json', kwargs={'slug': instance.cached_badgeclass.slug})

        representation['public_url'] = OriginSetting.HTTP+reverse('badgeinstance_json', kwargs={'slug': instance.slug})

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
        return self.context.get('badgeclass').issue(
            recipient_id=validated_data.get('recipient_identifier'),
            evidence_url=validated_data.get('evidence'),
            notify=validated_data.get('create_notification'),
            created_by=self.context.get('request').user,
            allow_uppercase=validated_data.get('allow_uppercase'),
            badgr_app=BadgrApp.objects.get_current(self.context.get('request'))
        )


class IssuerPortalSerializer(serializers.Serializer):
    """
    A serializer used to pass initial data to a view template so that the React.js
    front end can render.
    It should detect which of the core Badgr applications are installed and return
    appropriate contextual information.
    """

    def to_representation(self, user):
        view_data = {}

        user_issuers = user.cached_issuers()
        user_issuer_badgeclasses = user.cached_badgeclasses()

        issuer_data = IssuerSerializer(
            user_issuers,
            many=True,
            context=self.context
        )
        badgeclass_data = BadgeClassSerializer(
            user_issuer_badgeclasses,
            many=True,
            context=self.context
        )

        view_data['issuer_issuers'] = issuer_data.data
        view_data['issuer_badgeclasses'] = badgeclass_data.data
        view_data['installed_apps'] = installed_apps_list()

        return view_data
