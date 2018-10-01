import base64
from collections import OrderedDict

from rest_framework import serializers

from badgeuser.models import BadgeUser, TermsVersion
from badgeuser.utils import notify_on_password_change
from entity.serializers import DetailSerializerV2, BaseSerializerV2
from mainsite.models import BadgrApp
from mainsite.serializers import StripTagsCharField
from mainsite.validators import PasswordValidator


class BadgeUserEmailSerializerV2(DetailSerializerV2):
    email = serializers.EmailField()
    verified = serializers.BooleanField(read_only=True)
    primary = serializers.BooleanField(required=False)

    class Meta(DetailSerializerV2.Meta):
        apispec_definition = ('BadgeUserEmail', {
            'properties': OrderedDict([
                ('email', {
                    'type': "string",
                    'format': "email",
                    'description': "Email address associated with a BadgeUser",
                }),
                ('verified', {
                    'type': "boolean",
                    'description': "True if the email address has been verified",
                }),
                ('primary', {
                    'type': "boolean",
                    'description': "True for a single email address to receive email notifications",
                }),
            ])
        })


class BadgeUserSerializerV2(DetailSerializerV2):
    firstName = StripTagsCharField(source='first_name', max_length=30, allow_blank=True)
    lastName = StripTagsCharField(source='last_name', max_length=30, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False, validators=[PasswordValidator()])
    currentPassword = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    emails = BadgeUserEmailSerializerV2(many=True, source='email_items', required=False)
    agreedTermsVersion = serializers.IntegerField(source='agreed_terms_version', required=False)
    marketingOptIn = serializers.BooleanField(source='marketing_opt_in', required=False)

    class Meta(DetailSerializerV2.Meta):
        model = BadgeUser
        apispec_definition = ('BadgeUser', {
            'properties': OrderedDict([
                ('entityId', {
                    'type': "string",
                    'format': "string",
                    'description': "Unique identifier for this BadgeUser",
                }),
                ('entityType', {
                    'type': "string",
                    'format': "string",
                    'description': "\"BadgeUser\"",
                }),
                ('firstName', {
                    'type': "string",
                    'format': "string",
                    'description': "Given name",
                }),
                ('lastName', {
                    'type': "string",
                    'format': "string",
                    'description': "Family name",
                }),
            ]),
        })

    def update(self, instance, validated_data):
        password = validated_data.pop('password') if 'password' in validated_data else None
        current_password = validated_data.pop('currentPassword') if 'currentPassword' in validated_data else None
        super(BadgeUserSerializerV2, self).update(instance, validated_data)

        if password:
            if not current_password:
                raise serializers.ValidationError({'currrent_password': "Field is required"})
            if instance.check_password(current_password):
                instance.set_password(password)
                notify_on_password_change(instance)
            else:
                raise serializers.ValidationError({'currrent_password': "Incorrect password"})

        instance.badgrapp = BadgrApp.objects.get_current(request=self.context.get('request', None))

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super(BadgeUserSerializerV2, self).to_representation(instance)

        latest = TermsVersion.cached.cached_latest()
        if latest:
            representation['latestTermsVersion'] = latest.version
            if latest.version != instance.agreed_terms_version:
                representation['latestTermsDescription'] = latest.short_description

        if not self.context.get('isSelf'):
            fields_shown_only_to_self = ['emails']
            for f in fields_shown_only_to_self:
                if f in representation['result'][0]:
                    del representation['result'][0][f]
        return representation


class BadgeUserTokenSerializerV2(BaseSerializerV2):
    token = serializers.CharField(read_only=True, source='cached_token')

    class Meta:
        apispec_definition = ('BadgeUserToken', {
            'properties': OrderedDict([
                ('token', {
                    'type': "string",
                    'format': "string",
                    'description': "Access token to use in the Authorization header",
                }),
            ])
        })

    def update(self, instance, validated_data):
        # noop
        return instance



class ApplicationInfoSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True, source='get_visible_name')
    image = serializers.URLField(read_only=True, source='get_icon_url')
    website_url = serializers.URLField(read_only=True)
    clientId = serializers.CharField(read_only=True, source='application.client_id')


class AccessTokenSerializerV2(DetailSerializerV2):
    application = ApplicationInfoSerializer(source='applicationinfo')
    scope = serializers.CharField(read_only=True)
    expires = serializers.DateTimeField(read_only=True)
    created = serializers.DateTimeField(read_only=True)

    class Meta:
        apispec_definition = ('AccessToken', {})

