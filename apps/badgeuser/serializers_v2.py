from rest_framework import serializers

from badgeuser.utils import notify_on_password_change
from entity.serializers import DetailSerializerV2, BaseSerializerV2
from mainsite.serializers import StripTagsCharField


class BadgeUserSerializerV2(DetailSerializerV2):
    firstName = StripTagsCharField(source='first_name', max_length=30, allow_blank=True)
    lastName = StripTagsCharField(source='last_name', max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email')
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def update(self, instance, validated_data):
        validated_data.pop('primary_email')  # ignore requests to update email

        password = validated_data.pop('password')
        super(BadgeUserSerializerV2, self).update(instance, validated_data)

        if password:
            instance.set_password(password)
            notify_on_password_change(instance)

        instance.save()
        return instance


class BadgeUserTokenSerializerV2(BaseSerializerV2):
    token = serializers.CharField(read_only=True, source='cached_token')

    def update(self, instance, validated_data):
        # noop
        return instance
