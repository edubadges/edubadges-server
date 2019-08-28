from rest_framework import serializers
from signing.models import SymmetricKey
from signing import utils
from signing import tsob


class SymmetricKeySerializer(serializers.Serializer):

    password = serializers.CharField()

    class Meta:
       model = SymmetricKey
       fields = ('password_hash',)

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
        raise NotImplementedError

    def to_representation(self, instance):
        representation = {}
        representation['password_hash'] = instance.password_hash
        return representation
