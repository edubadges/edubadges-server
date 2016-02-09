from django.conf import settings

from allauth.account.models import EmailConfirmation, EmailAddress
from rest_framework import serializers
from rest_framework.authtoken.models import Token

#from earner.serializers import EarnerBadgeSerializer
#from consumer.serializers import ConsumerBadgeDetailSerializer

from .models import BadgeUser, CachedEmailAddress


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


class BadgeUserSerializer(serializers.ModelSerializer):
    """
    The BadgeUserSerializer brings together the necessary context information about
    a user's roles as Issuer, Earner, and Consumer
    """
    class Meta:
        model = BadgeUser
        fields = ('userProfile',)

    userProfile = UserProfileField(source='*', read_only=True)
    # earnerBadges = EarnerBadgeSerializer(many=True, read_only=True, source='earnerbadge_set')
    # consumerBadges = ConsumerBadgeDetailSerializer(many=True, read_only=True, source='consumerbadge_set')
    # issuerRoles


class BadgeUserProfileSerializer(serializers.Serializer):

    first_name = serializers.CharField(max_length=30, allow_blank=True)
    last_name = serializers.CharField(max_length=30, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def create(self, validated_data):
        request = self.context.get('request')

        try:
            email_address = EmailAddress.objects.get(email=validated_data['email'])
        except EmailAddress.DoesNotExist:
            pass
        else:
            if email_address.verified is False:
                email_address.delete()
            else:
                raise serializers.ValidationError(
                    'Account could not be created. An account with this email address may already exist.'
                )

        user = BadgeUser(
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        user.set_password(validated_data['password'])
        user.save()

        EmailAddress.objects.add_email(
            request, user, validated_data['email'], confirm=True, signup=True
        )

        return user

    # def update(self, instance, validated_data):
    #     if validated_data['first_name']:
    #         instance.first_name = validated_data['first_name']
    #     if validated_data['last_name']:
    #         instance.last_name = validated_data['last_name']
    #
    #     if validated_data.get('first_name', validated_data.get('last_name')):
    #         instance.save()
    #
    #     return instance


class NewEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary')
        read_only_fields = ('id', 'verified', 'primary')


class ExistingEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary')
        read_only_fields = ('id', 'email', 'verified')
