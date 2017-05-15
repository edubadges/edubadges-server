from rest_framework import serializers

from badgeuser.models import BadgeUser
from badgeuser.utils import notify_on_password_change
from entity.serializers import DetailSerializerV2, BaseSerializerV2
from mainsite.serializers import StripTagsCharField


class BadgeUserEmailSerializerV2(DetailSerializerV2):
    email = serializers.EmailField()
    verified = serializers.BooleanField(read_only=True)
    primary = serializers.BooleanField(required=False)


class BadgeUserSerializerV2(DetailSerializerV2):
    firstName = StripTagsCharField(source='first_name', max_length=30, allow_blank=True)
    lastName = StripTagsCharField(source='last_name', max_length=30, allow_blank=True)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    emails = BadgeUserEmailSerializerV2(many=True, source='email_items', required=False)

    class Meta(DetailSerializerV2.Meta):
        model = BadgeUser

    def update(self, instance, validated_data):
        password = validated_data.pop('password') if 'password' in validated_data else None
        super(BadgeUserSerializerV2, self).update(instance, validated_data)

        if password:
            instance.set_password(password)
            notify_on_password_change(instance)

        instance.save()
        return instance

    def to_representation(self, instance):
        representation = super(BadgeUserSerializerV2, self).to_representation(instance)
        if not self.context.get('isSelf'):
            fields_shown_only_to_self = ['emails']
            for f in fields_shown_only_to_self:
                if f in representation['result'][0]:
                    del representation['result'][0][f]
        return representation


class BadgeUserTokenSerializerV2(BaseSerializerV2):
    token = serializers.CharField(read_only=True, source='cached_token')

    def update(self, instance, validated_data):
        # noop
        return instance
