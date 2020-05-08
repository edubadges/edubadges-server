import datetime

import badgrlog
from django.core.exceptions import ValidationError as DjangoValidationError
from django.urls import reverse
from django.utils.dateparse import parse_datetime, parse_date
from issuer.helpers import BadgeCheckHelper
from issuer.models import BadgeInstance
from mainsite.drf_fields import Base64FileField
from mainsite.serializers import MarkdownCharField
from mainsite.utils import OriginSetting
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as RestframeworkValidationError
from rest_framework.fields import SkipField

logger = badgrlog.BadgrLogger()


class LocalBadgeInstanceUploadSerializerV1(serializers.Serializer):
    image = Base64FileField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    assertion = serializers.CharField(required=False, write_only=True)
    recipient_identifier = serializers.CharField(required=False, read_only=True)
    acceptance = serializers.CharField(default='Accepted')
    public = serializers.BooleanField(required=False, default=False)
    narrative = MarkdownCharField(required=False, read_only=True)

    extensions = serializers.DictField(source='extension_items', read_only=True)

    def to_representation(self, obj):
        """
        If the APIView initialized the serializer with the extra context
        variable 'format' from a query param in the GET request with the
        value "plain", make the `json` field for this instance read_only.
        """
        if self.context.get('format', 'v1') == 'plain':
            self.fields.json = serializers.DictField(read_only=True)
        representation = super(LocalBadgeInstanceUploadSerializerV1, self).to_representation(obj)

        representation['id'] = obj.entity_id
        representation['json'] = V1BadgeInstanceSerializer(obj, context=self.context).data
        representation['imagePreview'] = {
            "type": "image",
            "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('badgeclass_image', kwargs={'entity_id': obj.cached_badgeclass.entity_id}))
        }
        if obj.cached_issuer.image:
            representation['issuerImagePreview'] = {
                "type": "image",
                "id": "{}{}?type=png".format(OriginSetting.HTTP, reverse('issuer_image', kwargs={'entity_id': obj.cached_issuer.entity_id}))
            }

        if obj.image:
            representation['image'] = obj.image_url()

        representation['shareUrl'] = obj.share_url

        return representation

    def validate(self, data):
        """
        Ensure only one assertion input field given.
        """

        fields_present = ['image' in data, 'url' in data,
                          'assertion' in data and data.get('assertion')]
        if (fields_present.count(True) > 1):
            raise serializers.ValidationError(
                "Only one instance input field allowed.")

        return data

    def create(self, validated_data):
        owner = validated_data.get('created_by')
        try:
            instance, created = BadgeCheckHelper.get_or_create_assertion(
                url=validated_data.get('url', None),
                imagefile=validated_data.get('image', None),
                assertion=validated_data.get('assertion', None),
                created_by=owner,
            )
            if not created:
                if instance.acceptance == BadgeInstance.ACCEPTANCE_ACCEPTED:
                    raise RestframeworkValidationError([{'name': "DUPLICATE_BADGE", 'description': "You already have this badge in your backpack"}])
                instance.acceptance = BadgeInstance.ACCEPTANCE_ACCEPTED
                instance.save()
            owner.publish()  # update BadgeUser.cached_badgeinstances()
        except DjangoValidationError as e:
            raise RestframeworkValidationError(e.args[0])
        return instance

    def update(self, instance, validated_data):
        """ Updating acceptance status (to 'Accepted') is permitted as well as changing public status. """
        # Only locally issued badges will ever have an acceptance status other than 'Accepted'
        if instance.acceptance == 'Unaccepted' and validated_data.get('acceptance') == 'Accepted':
            instance.acceptance = 'Accepted'
            instance.save()
        public = validated_data.get('public', None)
        if public != None:
            instance.public = public
            instance.save()
        return instance


##
#
# the below exists to prop up V1BadgeInstanceSerializer for /v1/ backwards compatability
# in LocalBadgeInstanceUploadSerializer.  it was taken from composition/format.py and verifier/serializers/fields.py
# before those apps were deprecated
#
# [Wiggins June 2017]
##


class BadgePotentiallyEmptyField(serializers.Field):
    def get_attribute(self, instance):
        value = serializers.Field.get_attribute(self, instance)

        if value == '' or value is None or value == {}:
            if not self.required or not self.allow_blank:
                raise SkipField()
        return value

    def validate_empty_values(self, data):
        """
        If an empty value (empty string, null) exists in an optional
        field, SkipField.
        """
        (is_empty_value, data) = serializers.Field.validate_empty_values(self,
                                                                         data)

        if is_empty_value or data == '':
            if self.required:
                self.fail('required')
            raise SkipField()

        return (False, data)


class VerifierBadgeDateTimeField(BadgePotentiallyEmptyField, serializers.Field):

    default_error_messages = {
        'not_int_or_str': 'Invalid format. Expected an int or str.',
        'bad_str': 'Invalid format. String is not ISO 8601 or unix timestamp.',
        'bad_int': 'Invalid format. Unix timestamp is out of range.',
    }

    def to_internal_value(self, value):
        if isinstance(value, str):
            try:
                return datetime.datetime.utcfromtimestamp(float(value))
            except ValueError:
                pass

            result = parse_datetime(value)
            if not result:
                try:
                    result = datetime.datetime.combine(
                        parse_date(value), datetime.datetime.min.time()
                    )
                except (TypeError, ValueError):
                    self.fail('bad_str')
            return result
        elif isinstance(value, (int, float)):
            try:
                return datetime.datetime.utcfromtimestamp(value)
            except ValueError:
                self.fail('bad_int')
        else:
            self.fail('not_int_or_str')

    def to_representation(self, string_value):
        if isinstance(string_value, (str, int, float)):
            value = self.to_internal_value(string_value)
        else:
            value = string_value

        return value.isoformat()


class BadgeURLField(serializers.URLField):
    def to_representation(self, value):
        if self.context.get('format', 'v1') == 'v1':
            result = {
                'type': '@id',
                'id': value
            }
            if self.context.get('name') is not None:
                result['name'] = self.context.get('name')
            return result
        else:
            return value


class BadgeImageURLField(serializers.URLField):
    def to_representation(self, value):
        if self.context.get('format', 'v1') == 'v1':
            result = {
                'type': 'image',
                'id': value
            }
            if self.context.get('name') is not None:
                result['name'] = self.context.get('name')
            return result
        else:
            return value


class BadgeStringField(serializers.CharField):
    def to_representation(self, value):
        if self.context.get('format', 'v1') == 'v1':
            return {
                'type': 'xsd:string',
                '@value': value
            }
        else:
            return value


class BadgeEmailField(serializers.EmailField):
    def to_representation(self, value):
        if self.context.get('format', 'v1') == 'v1':
            return {
                'type': 'email',
                '@value': value
            }
        else:
            return value


class BadgeDateTimeField(VerifierBadgeDateTimeField):
    def to_representation(self, string_value):
        value = super(BadgeDateTimeField, self).to_representation(string_value)
        if self.context.get('format', 'v1') == 'v1':
            return {
                'type': 'xsd:dateTime',
                '@value': value
            }
        else:
            return value


class V1IssuerSerializer(serializers.Serializer):
    id = serializers.URLField(required=False)  # v0.5 Badge Classes have none
    type = serializers.CharField()
    name = BadgeStringField()
    url = BadgeURLField()
    description = BadgeStringField(required=False)
    image = BadgeImageURLField(required=False)
    email = BadgeEmailField(required=False)


class V1BadgeClassSerializer(serializers.Serializer):
    id = serializers.URLField(required=False)  # v0.5 Badge Classes have none
    type = serializers.CharField()
    name = BadgeStringField()
    description = BadgeStringField()
    image = BadgeImageURLField()
    criteria = BadgeURLField()
    criteria_text = BadgeStringField(required=False)
    criteria_url = BadgeURLField(required=False)
    issuer = V1IssuerSerializer()
    tags = serializers.ListField(child=BadgeStringField(), required=False)

    def to_representation(self, instance):
        representation = super(V1BadgeClassSerializer, self).to_representation(instance)
        if 'alignment' in instance:
            representation['alignment'] = instance['alignment']
        return representation


class V1InstanceSerializer(serializers.Serializer):
    id = serializers.URLField(required=False)
    type = serializers.CharField()
    uid = BadgeStringField(required=False)
    recipient = BadgeEmailField()  # TODO: improve for richer types
    badge = V1BadgeClassSerializer()
    issuedOn = BadgeDateTimeField(required=False) # missing in some translated v0.5.0
    expires = BadgeDateTimeField(required=False)
    image = BadgeImageURLField(required=False)


class V1BadgeInstanceSerializer(V1InstanceSerializer):
    """
    used to serialize a issuer.BadgeInstance like a composition.LocalBadgeInstance
    """
    def to_representation(self, instance):
        localbadgeinstance_json = instance.json
        localbadgeinstance_json['uid'] = instance.entity_id
        localbadgeinstance_json['badge'] = instance.cached_badgeclass.json
        localbadgeinstance_json['badge']['criteria'] = instance.cached_badgeclass.get_criteria_url()
        if instance.cached_badgeclass.criteria_text:
            localbadgeinstance_json['badge']['criteria_text'] = instance.cached_badgeclass.criteria_text
        if instance.cached_badgeclass.criteria_url:
            localbadgeinstance_json['badge']['criteria_url'] = instance.cached_badgeclass.criteria_url
        localbadgeinstance_json['badge']['issuer'] = instance.cached_issuer.json

        # clean up recipient to match V1InstanceSerializer
        localbadgeinstance_json['recipient'] = {
            "type": "email",
            "recipient": instance.recipient_identifier,
        }
        return super(V1BadgeInstanceSerializer, self).to_representation(localbadgeinstance_json)

