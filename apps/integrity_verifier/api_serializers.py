import json

from rest_framework import serializers

from . import RemoteBadgeInstance, AnalyzedBadgeInstance
from .utils import get_instance_url_from_image, get_instance_url_from_assertion


class IntegritySerializer(serializers.Serializer):
    recipient = serializers.CharField(required=True, source='recipient_id')

    assertion = serializers.DictField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    image = serializers.ImageField(required=False, write_only=True)

    json = serializers.DictField(read_only=True)
    version = serializers.CharField(read_only=True)
    errors = serializers.ListField(read_only=True, source='all_errors')
    badge = serializers.DictField(read_only=True)
    badge_url = serializers.URLField(read_only=True)
    issuer = serializers.DictField(read_only=True)
    issuer_url = serializers.URLField(read_only=True)

    def validate(self, data):
        instance_input_fields = set(('url', 'image', 'assertion'))
        valid_inputs = {key: data.get(key) for
                        key in instance_input_fields.intersection(data.keys())}

        if len(valid_inputs.keys()) != 1:
            raise serializers.ValidationError(
                "Only one instance input field allowed. Recieved "
                + json.dumps(valid_inputs.keys())
            )

        return data

    def create(self, validated_data):
        if validated_data.get('url') is not None:
            url = validated_data.get('url')
        elif validated_data.get('image') is not None:
            image = validated_data.get('image')
            image.open()
            url = get_instance_url_from_image(image)
        elif validated_data.get('assertion') is not None:
            url = get_instance_url_from_assertion(
                validated_data.get('assertion')
            )

        rbi = RemoteBadgeInstance(
            instance_url=url,
            recipient_id=validated_data.get('recipient_id')
        )

        abi = AnalyzedBadgeInstance(rbi)
        return abi
