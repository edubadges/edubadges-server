from rest_framework import serializers

from entity.serializers import DetailSerializerV2
from mainsite.serializers import StripTagsCharField
from .models import BadgeUser, CachedEmailAddress
from .utils import notify_on_password_change


class BadgeUserProfileSerializerV2(DetailSerializerV2):
    firstName = StripTagsCharField(source='first_name', max_length=30, allow_blank=True)
    lastName = StripTagsCharField(source='last_name', max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', )
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def create(self, validated_data):
        request = self.context.get('request')
        existing_user = None

        # Fetch existing email address if it is verified, delete unverified email address records.
        try:
            email_address = CachedEmailAddress.objects.get(email=validated_data['primary_email'])
        except CachedEmailAddress.DoesNotExist:
            email_address = None
        else:
            if email_address.verified is False:
                email_address.delete()
                email_address = None

        # Identify the user account if it is already partially initialized
        if email_address and not existing_user:
            existing_user = email_address.user
        else:
            # TODO: change this after deprecating the email database column for the BadgeUser model.
            existing_user = BadgeUser.objects.filter(email=validated_data['primary_email']).first()

        if existing_user:
            # if existing_user.password is NOT set, this user was auto-created and needs to be claimed
            if existing_user.password:
                raise serializers.ValidationError(
                    'Account could not be created. An account with this email address may already exist.'
                )
            user = existing_user
        else:
            user = BadgeUser(
                email=validated_data['primary_email']
            )

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.set_password(validated_data['password'])
        user.save()

        if not email_address:
            CachedEmailAddress.objects.add_email(
                request, user, validated_data['primary_email'], confirm=True, signup=True
            )
        else:
            email_address.send_confirmation(request, signup=True)

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
        representation = super(BadgeUserProfileSerializerV2, self).to_representation(instance)

        if self.context.get('include_token', False):
            representation['token'] = instance.cached_token()

        return representation