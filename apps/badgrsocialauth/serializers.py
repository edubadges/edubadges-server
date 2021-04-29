from rest_framework import serializers


class BadgrSocialAccountSerializerV1(serializers.Serializer):
    id = serializers.CharField()
    provider = serializers.CharField()
    dateAdded = serializers.DateTimeField(source='date_joined')
    uid = serializers.CharField()

    def to_representation(self, instance):
        representation = super(BadgrSocialAccountSerializerV1, self).to_representation(instance)
        provider = instance.get_provider()
        extra_data = instance.extra_data
        common_fields = provider.extract_common_fields(extra_data)
        email = common_fields.get('email', None)
        if not email and 'userPrincipalName' in extra_data:
            email = extra_data['userPrincipalName']
        representation.update({
            'firstName': common_fields.get('first_name', None),
            'lastName': common_fields.get('last_name', None),
            'preferredUsername': common_fields.get('preferred_username', None),
            'primaryEmail': email,
            'eduid': extra_data.get('eduid', None)
        })

        return representation
