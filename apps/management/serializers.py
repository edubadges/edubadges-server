from django.contrib.auth.models import Group
from rest_framework import serializers
from mainsite.serializers import StripTagsCharField


class GroupSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')

    class Meta:
        model = Group
        fields = ('name', 'slug')

    def to_representation(self, instance):
        return super(GroupSerializer, self).to_representation(instance)


class BadgeClassSerializerStatistics(serializers.Serializer):
    name = StripTagsCharField(max_length=255, read_only=True)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')
    description = StripTagsCharField(max_length=16384, convert_null=True, read_only=True)

    class Meta:
        apispec_definition = ('BadgeClass', {})

    def to_representation(self, instance):
        representation = super(BadgeClassSerializerStatistics, self).to_representation(instance)
        representation['assertion_count'] = instance.badgeinstances.all().__len__()
        instance_json = instance.get_json(obi_version='1_1', use_canonical_id=True)
        representation['image'] = instance_json['image']
        return representation


class IssuerSerializerStatistics(serializers.Serializer):
    name = StripTagsCharField(max_length=255, read_only=True)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')
    description = StripTagsCharField(max_length=16384, convert_null=True, read_only=True)
    badgeclasses = BadgeClassSerializerStatistics(many=True, read_only=True)

    class Meta:
        apispec_definition = ('Issuer', {})

    def to_representation(self, instance):
        representation = super(IssuerSerializerStatistics, self).to_representation(instance)
        instance_json = instance.get_json(obi_version='1_1', use_canonical_id=True)
        image = instance_json.get('image', None)
        representation['image'] = image
        return representation


class FacultySerializerStatistics(serializers.Serializer):
    name = StripTagsCharField(max_length=255, read_only=True)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')
    # issuers = IssuerSerializerStatistics(many=True, read_only=True)

    class Meta:
        apispec_definition = ('Faculty', {})

    def to_representation(self, instance):
        representation = super(FacultySerializerStatistics, self).to_representation(instance)
        representation['issuers'] = [IssuerSerializerStatistics().to_representation(issuer) for issuer in instance.issuer_set.all()]
        return representation