# Created by wiggins@concentricsky.com on 3/31/16.
from collections import OrderedDict

from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from mainsite.serializers import LinkedDataReferenceField, LinkedDataEntitySerializer, LinkedDataReferenceList, \
    StripTagsCharField
from mainsite.utils import OriginSetting
from pathway.models import Pathway
from recipient.models import RecipientGroup, RecipientGroupMembership, RecipientProfile


class RecipientProfileSerializerV1(serializers.Serializer):

    def to_representation(self, instance):
        representation = super(RecipientProfileSerializerV1, self).to_representation(instance)
        representation.update([
            ('@id', u"mailto:{}".format(instance.recipient_identifier)),
            ('@type', "RecipientProfile"),
            ('slug', instance.entity_id),
            ('name', instance.display_name),
            ('email', instance.recipient_identifier)
        ])
        return representation


class RecipientGroupMembershipSerializerV1(LinkedDataEntitySerializer):
    jsonld_type = "RecipientGroupMembership"

    email = serializers.EmailField(write_only=True, source='recipient_identifier')
    name = StripTagsCharField(source='membership_name')
    slug = StripTagsCharField(source='recipient_profile.entity_id', read_only=True)

    def to_representation(self, instance):
        json = super(RecipientGroupMembershipSerializerV1, self).to_representation(instance)
        json.update([('email', instance.recipient_identifier)])

        return json

    def to_internal_value(self, data):
        membership = None

        if not 'recipient_group' in self.context:
            raise ValidationError(
                "RecipientGroup must be present in the context to identify a RecipientProfile."
            )

        try:
            profile = RecipientProfile.objects.get(recipient_identifier=data.get('email'))
            exists = True
        except RecipientProfile.DoesNotExist:
            profile = RecipientProfile(
                recipient_identifier=data.get('email'),
                display_name=data.get('name')
            )
            exists = False

        if exists:
            try:
                membership = RecipientGroupMembership.objects.get(
                    recipient_profile=profile,
                    recipient_group=self.context.get('recipient_group')
                )
                if membership.membership_name != data.get('name'):
                    membership.membership_name = data.get('name')
                    membership.save()
            except RecipientGroupMembership.DoesNotExist:
                pass

        if not membership:
            membership = RecipientGroupMembership(
                recipient_profile=profile,
                recipient_group=self.context.get('recipient_group'),
                membership_name=data.get('name')
            )

        return membership


class RecipientGroupMembershipListSerializerV1(serializers.Serializer):
    def to_representation(self, memberships):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        recipient_group_slug = self.context.get('recipient_group_slug', None)
        if not recipient_group_slug:
            raise ValidationError("Invalid recipient_group_slug")

        members_serializer = RecipientGroupMembershipSerializerV1(memberships, many=True, context=self.context)
        return OrderedDict([
            ("@context", OriginSetting.HTTP+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupMembershipList"),
            ("recipientGroup", OriginSetting.HTTP+reverse('v1_api_recipient_group_detail', kwargs={'issuer_slug': issuer_slug, 'slug': recipient_group_slug})),
            ("memberships", members_serializer.data),
        ])


class RecipientGroupSerializerV1(LinkedDataEntitySerializer):
    jsonld_type = "RecipientGroup"

    name = StripTagsCharField(required=False)
    description = StripTagsCharField(required=False)
    slug = StripTagsCharField(read_only=True, source='entity_id')
    active = serializers.BooleanField(source='is_active', default=True)
    issuer = LinkedDataReferenceField(keys=['slug'], field_names={'slug': 'entity_id'}, model=Issuer)
    member_count = serializers.IntegerField(read_only=True)
    members = RecipientGroupMembershipSerializerV1(
        read_only=False, many=True, required=False, source='cached_members'
    )
    pathways = LinkedDataReferenceList(
        read_only=False, required=False, source='cached_pathways',
        child=LinkedDataReferenceField(read_only=False, keys=['slug'], model=Pathway)
    )

    def to_representation(self, instance):
        if not self.context.get('embedRecipients', False) and 'members' in self.fields:
            self.fields.pop('members')

        return super(RecipientGroupSerializerV1, self).to_representation(instance)

    def create(self, validated_data):
        if 'issuer' not in self.context:
            raise ValidationError("No issuer")
        issuer = self.context.get('issuer')

        name = validated_data.get('name')
        description = validated_data.get('description', '')

        recipient_group = RecipientGroup(
            issuer=issuer,
            name=name,
            is_active=validated_data.get('is_active', True)
        )
        if description:
            recipient_group.description = description
        recipient_group.save()
        return recipient_group

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get('description', instance.description)
        instance.is_active = validated_data.get('is_active', instance.is_active)

        if 'cached_pathways' in validated_data:
            existing_pathway_ids = set(instance.cached_pathways())
            updated_pathway_ids = set(validated_data.get('cached_pathways'))

            pathways_to_delete = existing_pathway_ids - updated_pathway_ids
            pathways_to_add = updated_pathway_ids - existing_pathway_ids

            for p in pathways_to_delete:
                instance.pathways.remove(p)
                p.publish()

            for p in pathways_to_add:
                instance.pathways.add(p)
                p.publish()

        if 'cached_members' in validated_data:
            existing_members = set(instance.cached_members())
            updated_members = set()

            for m in validated_data.get('cached_members'):
                # Save any newly defined profiles directly to the list,
                # save existing members for comparison
                if m.pk:
                    updated_members.add(m)
                else:
                    if not m.recipient_profile.pk:
                        m.recipient_profile.save()
                        m.recipient_profile_id = m.recipient_profile.pk
                    m.save()

            members_to_delete = existing_members - updated_members

            for m in members_to_delete:
                m.delete()

        instance.save() # update cache
        return instance


class IssuerRecipientGroupListSerializerV1(serializers.Serializer):
    def to_representation(self, issuer):
        issuer_slug = issuer.slug
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        groups_serializer = RecipientGroupSerializerV1(issuer.recipientgroup_set.all(), many=True, context=self.context)
        return OrderedDict([
            ("@context", OriginSetting.HTTP+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupList"),
            ("issuer", OriginSetting.HTTP+reverse('issuer_json', kwargs={'entity_id': issuer_slug})),
            ("recipientGroups", groups_serializer.data)
        ])
