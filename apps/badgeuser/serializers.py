from django.conf import settings
from rest_framework import serializers

from mainsite.serializers import StripTagsCharField
from .models import BadgeUser, CachedEmailAddress
from .utils import notify_on_password_change


class BadgeUserTokenSerializerV1(serializers.Serializer):
    def to_representation(self, instance):
        representation = {
            'username': instance.username,
            'token': instance.cached_token()
        }
        return representation

    def update(self, instance, validated_data):
        # noop
        return instance


class VerifiedEmailsField(serializers.Field):
    def to_representation(self, obj):
        addresses = []
        for emailaddress in obj.all():
            addresses.append(emailaddress.email)
        return addresses


class BadgeUserProfileSerializer(serializers.Serializer):
    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', )
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def create(self, validated_data):
        user = BadgeUser.objects.create(
            email=validated_data['primary_email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            plaintext_password=validated_data['password']
        )
        return user

    def update(self, user, validated_data):
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        password = validated_data.get('password')
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if password:
            user.set_password(password)
            notify_on_password_change(user)

        user.save()
        return user

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializer, self).to_representation(instance)

        if self.context.get('include_token', False):
            representation['token'] = instance.cached_token()

        return representation


class EmailSerializer(serializers.ModelSerializer):
    variants = serializers.ListField(
        child=serializers.EmailField(required=False),
        required=False, source='cached_variants', allow_null=True, read_only=True
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary', 'variants')
        read_only_fields = ('id', 'verified', 'primary', 'variants')

    def create(self, validated_data):
        new_address = validated_data.get('email')
        created = False
        try:
            email = CachedEmailAddress.objects.get(email=new_address)
        except CachedEmailAddress.DoesNotExist:
            email = super(EmailSerializer, self).create(validated_data)
            created = True
        else:
            if not email.verified:
                # Clear out a previous attempt and let the current user try
                email.delete()
                email = super(EmailSerializer, self).create(validated_data)
                created = True
            elif email.user != self.context.get('request').user:
                raise serializers.ValidationError("Could not register email address.")

        if new_address != email.email and new_address not in [v.email for v in email.cached_variants()]:
            email.add_variant(new_address)
            raise serializers.ValidationError("Matching address already exists. New case variant registered.")

        if validated_data.get('variants'):
            for variant in validated_data.get('variants'):
                try:
                    email.add_variant(variant)
                except serializers.ValidationError:
                    pass
        if created:
            return email

        raise serializers.ValidationError("Could not register email address.")


class BadgeUserIdentifierField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'created_by_id'
        if 'read_only' not in kwargs:
            kwargs['read_only'] = True
        super(BadgeUserIdentifierField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return BadgeUser.cached.get(pk=value).primary_email
        except BadgeUser.DoesNotExist:
            return None