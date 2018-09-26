from django.conf import settings
from rest_framework import serializers

from mainsite.models import BadgrApp
from mainsite.serializers import StripTagsCharField
from mainsite.validators import PasswordValidator
from .models import BadgeUser, CachedEmailAddress, TermsVersion
from .utils import notify_on_password_change


class BadgeUserTokenSerializerV1(serializers.Serializer):
    class Meta:
        apispec_definition = ('BadgeUserToken', {})

    def to_representation(self, instance):
        representation = {
            'username': instance.username,
            'token': instance.cached_token()
        }
        if self.context.get('tokenReplaced', False):
            representation['replace'] = True
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


class BadgeUserProfileSerializerV1(serializers.Serializer):
    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', required=False)
    current_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False, validators=[PasswordValidator()])
    slug = serializers.CharField(source='entity_id', read_only=True)
    agreed_terms_version = serializers.IntegerField(required=False)
    marketing_opt_in = serializers.BooleanField(required=False)

    class Meta:
        apispec_definition = ('BadgeUser', {})

    def create(self, validated_data):
        user = BadgeUser.objects.create(
            email=validated_data['primary_email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            plaintext_password=validated_data['password'],
            marketing_opt_in=validated_data.get('marketing_opt_in', False),
            request=self.context.get('request', None),
        )
        return user

    def update(self, user, validated_data):
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        password = validated_data.get('password')
        current_password = validated_data.get('current_password')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if password:
            if not current_password:
                raise serializers.ValidationError({'currrent_password': "Field is required"})
            if user.check_password(current_password):
                user.set_password(password)
                notify_on_password_change(user)
            else:
                raise serializers.ValidationError({'currrent_password': "Incorrect password"})

        if 'agreed_terms_version' in validated_data:
            user.agreed_terms_version = validated_data.get('agreed_terms_version')

        if 'marketing_opt_in' in validated_data:
            user.marketing_opt_in = validated_data.get('marketing_opt_in')

        user.save()
        return user

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializerV1, self).to_representation(instance)

        if self.context.get('include_token', False):
            representation['token'] = instance.cached_token()

        latest = TermsVersion.cached.cached_latest()
        if latest:
            representation['latest_terms_version'] = latest.version
            if latest.version != instance.agreed_terms_version:
                representation['latest_terms_description'] = latest.short_description

        return representation


class EmailSerializerV1(serializers.ModelSerializer):
    variants = serializers.ListField(
        child=serializers.EmailField(required=False),
        required=False, source='cached_variants', allow_null=True, read_only=True
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary', 'variants')
        read_only_fields = ('id', 'verified', 'primary', 'variants')
        apispec_definition = ('BadgeUserEmail', {

        })

    def create(self, validated_data):
        new_address = validated_data.get('email')
        created = False
        try:
            email = CachedEmailAddress.objects.get(email=new_address)
        except CachedEmailAddress.DoesNotExist:
            email = super(EmailSerializerV1, self).create(validated_data)
            created = True
        else:
            if not email.verified:
                # Clear out a previous attempt and let the current user try
                email.delete()
                email = super(EmailSerializerV1, self).create(validated_data)
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


class BadgeUserIdentifierFieldV1(serializers.CharField):
    def __init__(self, *args, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'created_by_id'
        if 'read_only' not in kwargs:
            kwargs['read_only'] = True
        super(BadgeUserIdentifierFieldV1, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return BadgeUser.cached.get(pk=value).primary_email
        except BadgeUser.DoesNotExist:
            return None

