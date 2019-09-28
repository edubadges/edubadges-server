from rest_framework import serializers
from signing.models import SymmetricKey
from signing import utils
from signing import tsob


class SymmetricKeySerializer(serializers.Serializer):

    password = serializers.CharField(required=False, allow_null=True)
    old_password = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = SymmetricKey

    def create(self, validated_data, **kwargs):
        if SymmetricKey.objects.filter(user=validated_data['created_by']).exists():
            raise serializers.ValidationError('User already has a SymmetricKey')
        symkey = tsob.create_new_symmetric_key(validated_data.get('password')).json()
        symkey = SymmetricKey.objects.create(
            password_hash=utils.hash_string(validated_data.get('password')),
            salt=symkey['salt'],
            length=symkey['length'],
            n=symkey['n'],
            r=symkey['r'],
            p=symkey['p'],
            current=True,
            user=validated_data['created_by']
        )
        return symkey

    def update(self, instance, validated_data):
        new_symkey = tsob.create_new_symmetric_key(validated_data.get('password')).json()
        new_symkey = SymmetricKey.objects.create(
            password_hash=utils.hash_string(validated_data.get('password')),
            salt=new_symkey['salt'],
            length=new_symkey['length'],
            n=new_symkey['n'],
            r=new_symkey['r'],
            p=new_symkey['p'],
            current=False,
            user=validated_data['updated_by']
        )
        try:
            tsob.re_encrypt_private_keys(old_symmetric_key=instance,
                                         new_symmetric_key=new_symkey,
                                         old_password=validated_data.get('old_password'),
                                         new_password=validated_data.get('password'))
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
