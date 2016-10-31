from django.conf import settings
from rest_framework import serializers

from mainsite.serializers import StripTagsCharField
from .models import BadgeUser, CachedEmailAddress
from .utils import notify_on_password_change


class VerifiedEmailsField(serializers.Field):
    def to_representation(self, obj):
        addresses = []
        for emailaddress in obj.all():
            addresses.append(emailaddress.email)
        return addresses


class UserProfileField(serializers.Serializer):
    """
    Receives the entire BadgeUser instance and returns a dict
    with profile information
    """
    def to_representation(self, obj):
        addresses = []
        if hasattr(obj, 'cached_email'):
            # BadgeUser
            for emailaddress in obj.cached_emails():
                addresses.append(emailaddress.email)
        elif hasattr(obj, 'email'):
            # AnonymousLtiUser
            addresses = [obj.email]
        elif obj.id is None:
            # AnonymousUser
            return {
                'name': "anonymous",
                'username': "",
                'earnerIds': [],
            }

        profile = {
            'name': obj.get_full_name(),
            'username': obj.username,
            'earnerIds': addresses
        }

        if self.context.get('include_token', False):
            profile['token'] = obj.cached_token()

        if getattr(settings, 'BADGR_APPROVED_ISSUERS_ONLY', False):
            profile['approvedIssuer'] = obj.has_perm('issuer.add_issuer')
        else:
            profile['approvedIssuer'] = True

        return profile


class BadgeUserProfileSerializer(serializers.Serializer):

    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def create(self, validated_data):
        request = self.context.get('request')

        try:
            email_address = CachedEmailAddress.objects.get(email=validated_data['email'])
        except CachedEmailAddress.DoesNotExist:
            pass
        else:
            if email_address.verified is False:
                email_address.delete()
            else:
                raise serializers.ValidationError(
                    'Account could not be created. An account with this email address may already exist.'
                )

        existing_user = BadgeUser.objects.filter(email=validated_data['email']).first()
        if existing_user:
            # if existing_user.password is NOT set, this user was auto-created and needs to be claimed
            if existing_user.password:
                raise serializers.ValidationError(
                    'Account could not be created. An account with this email address may already exist.'
                )
            user = existing_user
        else:
            user = BadgeUser(
                email=validated_data['email']
            )

        user.first_name = validated_data['first_name']
        user.last_name = validated_data['last_name']
        user.set_password(validated_data['password'])
        user.save()

        CachedEmailAddress.objects.add_email(
            request, user, validated_data['email'], confirm=True, signup=True
        )

        return user


class BadgeUserExistingProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)

    class Meta:
        model = BadgeUser
        fields = ('id', 'first_name', 'email', 'last_name', 'password')
        write_only_fields = ('password',)
        read_only_fields = ('id', 'email',)

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


class NewEmailSerializer(serializers.ModelSerializer):
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
        try:
            email = CachedEmailAddress.objects.get(email=new_address)
        except CachedEmailAddress.DoesNotExist:
            email = super(NewEmailSerializer, self).create(validated_data)
        else:
            if not email.verified:
                # Clear out a previous attempt and let the current user try
                email.delete()
                email = super(NewEmailSerializer, self).create(validated_data)

        if new_address != email.email and new_address not in [v.email for v in email.cached_variants()]:
            email.add_variant(new_address)
            raise serializers.ValidationError("Matching address already exists. New case variant registered.")

        if validated_data.get('variants'):
            for variant in validated_data.get('variants'):
                try:
                    email.add_variant(variant)
                except serializers.ValidationError:
                    pass

        return email


class ExistingEmailSerializer(serializers.ModelSerializer):
    variants = serializers.ListField(
        child=serializers.EmailField(required=False),
        required=False, source='cached_variants', allow_null=True, read_only=True
    )

    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary', 'variants')
        read_only_fields = ('id', 'email', 'verified', 'variants')
