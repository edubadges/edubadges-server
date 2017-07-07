from rest_framework import serializers


class BadgrSocialAccountSerializerV1(serializers.Serializer):
    id = serializers.CharField()
    provider = serializers.CharField()
    dateAdded = serializers.DateTimeField(source='date_joined')
    uid = serializers.CharField()

    def to_representation(self, instance):
        representation = super(BadgrSocialAccountSerializerV1, self).to_representation(instance)
        provider = instance.get_provider()
        common_fields = provider.extract_common_fields(instance.extra_data)

        representation.update({
            'firstName': common_fields.get('first_name', None),
            'lastName': common_fields.get('last_name', None),
            'primaryEmail': common_fields.get('email', None),
        })

        return representation
