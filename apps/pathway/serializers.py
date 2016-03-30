# Created by wiggins@concentricsky.com on 3/30/16.
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from pathway.models import Pathway, PathwayElement


class PathwaySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, read_only=True)
    issuer = serializers.HyperlinkedRelatedField(view_name='issuer_json', read_only=True, lookup_field='slug')
    name = serializers.CharField(max_length=254, write_only=True)
    description = serializers.CharField(write_only=True)

    def to_representation(self, instance):
        representation = super(PathwaySerializer, self).to_representation(instance)
        representation.update({
            'name': instance.cached_root_element.name,
            'description': instance.cached_root_element.description,
        })
        return representation

    def create(self, validated_data, **kwargs):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Could not determine issuer")
        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            raise ValidationError("Could not determine issuer")

        pathway = Pathway(issuer=issuer)
        pathway.save()
        root_element = PathwayElement(
            pathway=pathway,
            parent_element=None,
            name=validated_data.get('name'),
            description=validated_data.get('description'),
        )
        root_element.save()
        pathway.root_element = root_element
        pathway.save()
        return pathway

    def update(self, instance, validated_data):
        pass




