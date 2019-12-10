from rest_framework import serializers
from signing import tsob
from signing.models import SymmetricKey, PrivateKey


class SymmetricKeySerializer(serializers.Serializer):

    password = serializers.CharField(required=False, allow_null=True)
    old_password = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = SymmetricKey

    def create(self, validated_data, **kwargs):
        if SymmetricKey.objects.filter(user=validated_data['created_by']).exists():
            raise serializers.ValidationError('User already has a SymmetricKey')
        symkey = tsob.create_new_symmetric_key(password=validated_data.get('password'),
                                               user=validated_data['created_by'])
        symkey.current = True
        symkey.save()
        return symkey

    def update(self, instance, validated_data):
        try:
            instance.validate_password(validated_data.get('old_password'))
        except ValueError as e:
            raise serializers.ValidationError(e.message)
        new_symkey = tsob.create_new_symmetric_key(password=validated_data.get('password'),
                                                   user=validated_data['updated_by'])
        try:
            private_keys_to_reencrypt = list(PrivateKey.objects.filter(symmetric_key=instance))
            if private_keys_to_reencrypt:
                tsob.re_encrypt_private_keys(
                    old_symmetric_key=instance,
                    new_symmetric_key=new_symkey,
                    old_password=validated_data.get('old_password'),
                    new_password=validated_data.get('password'),
                    private_key_list=private_keys_to_reencrypt
                )
            instance.current = False
            instance.save()
            new_symkey.current = True
            new_symkey.save()
        except ValueError as e:
            new_symkey.delete()
            raise serializers.ValidationError(e.message)
        return new_symkey

    def to_representation(self, instance):
        if instance:
            return {'exists': True}
        if not instance:
            return {'exists': False}
