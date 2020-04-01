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
        email = common_fields.get('email', None)
        if not email and 'userPrincipalName' in instance.extra_data:
            email = instance.extra_data['userPrincipalName']
        entitlements = instance.extra_data.get('eduperson_entitlement', [])
        verified_by_institution = "urn:mace:eduid.nl:entitlement:verified-by-institution" in entitlements
        representation.update({
            'firstName': common_fields.get('first_name', None),
            'lastName': common_fields.get('last_name', None),
            'primaryEmail': email,
            'verified_by_institution': verified_by_institution
        })

        return representation
