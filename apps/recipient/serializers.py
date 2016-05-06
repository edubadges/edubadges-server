# Created by wiggins@concentricsky.com on 3/31/16.
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from mainsite.serializers import LinkedDataReferenceField, LinkedDataEntitySerializer
from recipient.models import RecipientGroup
from pathway.models import Pathway


class RecipientProfileSerializer(serializers.Serializer):

    def to_representation(self, instance):
        representation = super(RecipientProfileSerializer, self).to_representation(instance)
        representation.update([
            ('@id', u"mailto:{}".format(instance.recipient_identifier)),
            ('@type', "RecipientProfile"),
            ('slug', instance.slug),
            ('name', instance.display_name),
        ])
        return representation


class RecipientGroupMembershipSerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(RecipientGroupMembershipSerializer, self).to_representation(instance)
        representation.update([
            ('@id', u"mailto:{}".format(instance.recipient_profile.recipient_identifier)),
            ('@type', "RecipientProfile"),
            ('slug', instance.recipient_profile.slug),
            ('name', instance.membership_name),
        ])
        return representation


class RecipientGroupMembershipListSerializer(serializers.Serializer):
    def to_representation(self, memberships):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        recipient_group_slug = self.context.get('recipient_group_slug', None)
        if not recipient_group_slug:
            raise ValidationError("Invalid recipient_group_slug")

        members_serializer = RecipientGroupMembershipSerializer(memberships, many=True, context=self.context)
        return OrderedDict([
            ("@context", settings.HTTP_ORIGIN+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupMembershipList"),
            ("recipientGroup", settings.HTTP_ORIGIN+reverse('recipient_group_detail', kwargs={'issuer_slug': issuer_slug, 'group_slug': recipient_group_slug})),
            ("memberships", members_serializer.data),
        ])


class RecipientGroupSerializer(LinkedDataEntitySerializer):
    jsonld_type = "RecipientGroup"

    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    slug = serializers.CharField(read_only=True)
    issuer = LinkedDataReferenceField(['slug'], Issuer)
    member_count = serializers.IntegerField(read_only=True)
    members = RecipientGroupMembershipSerializer(many=True, source='cached_members')
    pathways = LinkedDataReferenceField(['slug'], Pathway, many=True)

    def to_representation(self, instance):
        if not self.context.get('embedRecipients', False):
            self.fields.pop('members')

        return super(RecipientGroupSerializer, self).to_representation(instance)

    def create(self, validated_data):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("No issuer")
        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            raise ValidationError("No issuer")

        name = validated_data.get('name')
        description = validated_data.get('description', '')

        recipient_group = RecipientGroup(issuer=issuer, name=name)
        if description:
            recipient_group.description = description
        recipient_group.save()
        return recipient_group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)

        if validated_data.get('pathways'):
            existing_pathway_ids = set(instance.cached_pathways())
            updated_pathway_ids = set(validated_data.get('pathways'))

            pathways_to_delete = existing_pathway_ids - updated_pathway_ids
            pathways_to_add = updated_pathway_ids - existing_pathway_ids

            for p in pathways_to_delete:
                instance.pathways.remove(p)

            for p in pathways_to_add:
                instance.pathways.add(p)

        if validated_data.get('members'):
            existing_member_slugs = set([i.jsonld_id for i in instance.cached_members])
            updated_pathway_ids = set(validated_data.get('members'))

            pathways_to_delete = existing_pathway_ids - updated_pathway_ids
            pathways_to_add = updated_pathway_ids - existing_pathway_ids

            for p in pathways_to_delete:
                path = Pathway.cached.get_by_slug_or_id(p)
                instance.pathways.remove(p)

            for p in pathways_to_add:
                path = Pathway.cached.get_by_slug_or_id(p)
                instance.pathways.add(p)

        instance.save()
        return instance

class RecipientGroupListSerializer(serializers.Serializer):
    def to_representation(self, recipient_groups):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        groups_serializer = RecipientGroupSerializer(recipient_groups, many=True, context=self.context)
        return OrderedDict([
            ("@context", settings.HTTP_ORIGIN+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupList"),
            ("issuer", settings.HTTP_ORIGIN+reverse('issuer_json', kwargs={'slug': issuer_slug})),
            ("recipientGroups", groups_serializer.data)
        ])
