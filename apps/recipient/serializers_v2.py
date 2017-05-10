# encoding: utf-8
from __future__ import unicode_literals

from rest_framework import serializers

from entity.serializers import DetailSerializerV2, EntityRelatedFieldV2
from issuer.serializers_v2 import BadgeRecipientSerializerV2
from mainsite.serializers import StripTagsCharField
from pathway.models import Pathway
from recipient.models import RecipientGroup, RecipientProfile


class RecipientGroupMembershipSerializerV2(DetailSerializerV2):
    recipient = BadgeRecipientSerializerV2(source='*')
    name = StripTagsCharField(source='membership_name')


class RecipientGroupSerializerV2(DetailSerializerV2):
    createdAt = serializers.DateTimeField(source='created_at', read_only=True)
    createdBy = EntityRelatedFieldV2(source='cached_creator', read_only=True)
    issuer = EntityRelatedFieldV2(source='cached_issuer', read_only=True)

    name = StripTagsCharField(required=False)
    description = StripTagsCharField(required=False)
    active = serializers.BooleanField(source='is_active', default=True)

    members = RecipientGroupMembershipSerializerV2(many=True, source='membership_items', required=False)
    pathways = EntityRelatedFieldV2(many=True, source='pathway_items', required=False, queryset=Pathway.cached)

    class Meta:
        model = RecipientGroup

    def update(self, instance, validated_data):
        if 'cached_issuer' in validated_data:
            validated_data.pop('cached_issuer')  # issuer is not updatedable
        super(RecipientGroupSerializerV2, self).update(instance, validated_data)

    def create(self, validated_data):
        if 'cached_issuer' in validated_data:
            # included issuer in request
            validated_data['issuer'] = validated_data.pop('cached_issuer')
        elif 'issuer' in self.context:
            # issuer was passed in context
            validated_data['issuer'] = self.context.get('issuer')
        else:
            # issuer is required on create
            raise serializers.ValidationError({"issuer": "This field is required"})

        return super(RecipientGroupSerializerV2, self).create(validated_data)

