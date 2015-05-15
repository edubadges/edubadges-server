import json

from django.core.exceptions import ValidationError as DjangoValidationError

from rest_framework import serializers

from integrity_verifier import RemoteBadgeInstance, AnalyzedBadgeInstance
from integrity_verifier.utils import get_instance_url_from_image, get_instance_url_from_assertion
from credential_store.models import StoredBadgeInstance

from .models import Collection

RECIPIENT_ERROR = {
    'recipient':
    "Badge recipient was not among any of user's confirmed identifiers"
}


class EarnerBadgeSerializer(serializers.Serializer):
    recipient_id = serializers.CharField(required=False)
    id = serializers.IntegerField(required=False)

    assertion = serializers.DictField(required=False, write_only=True)
    url = serializers.URLField(required=False, write_only=True)
    image = serializers.ImageField(required=False, write_only=True)

    json = serializers.DictField(read_only=True)
    errors = serializers.ListField(read_only=True)

    def validate(self, data):
        # Remove empty DictField
        if data.get('assertion') == {}:
            data.pop('assertion', None)

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
        user = self.context.get('request').user

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

        try:
            rbi = RemoteBadgeInstance(url)
        except DjangoValidationError as e:
            raise e

        abi = AnalyzedBadgeInstance(rbi, recipient_ids=[id.email for id in user.emailaddress_set.all()])
        if len(
            [x for x in abi.non_component_errors if x[0] == 'error.recipient']
        ) != 0:
            raise serializers.ValidationError(RECIPIENT_ERROR)

        if not abi.is_valid():
            raise serializers.ValidationError(abi.all_errors())
        else:
            new_instance = StoredBadgeInstance.from_analyzed_instance(
                abi, **{'recipient_user': user}
            )

            return new_instance


class EarnerBadgeReferenceSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)


class CollectionSerializer(serializers.Serializer):
    name = serializers.CharField(required=True, max_length=128)
    slug = serializers.CharField(required=False, max_length=128)
    description = serializers.CharField(required=False, max_length=255)
    badges = serializers.ListField(
        required=False, child=EarnerBadgeReferenceSerializer(),
        source='instances.all'
    )

    def create(self, validated_data):
        user = self.context.get('request').user

        new_collection = Collection(
            name=validated_data.get('name'),
            slug=validated_data.get('slug', None),
            description=validated_data.get('description', ''),
            recipient=user
        )

        if validated_data.get('badges') is not None:
            raise NotImplementedError("Adding badges to collection on creation not implemented.")

        new_collection.save()
        return new_collection
