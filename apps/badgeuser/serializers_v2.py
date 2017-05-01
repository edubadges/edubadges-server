from rest_framework import serializers

from entity.serializers import DetailSerializerV2
from mainsite.serializers import StripTagsCharField
from .utils import notify_on_password_change


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

