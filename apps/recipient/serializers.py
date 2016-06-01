# Created by wiggins@concentricsky.com on 3/31/16.
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from mainsite.serializers import LinkedDataReferenceField, LinkedDataEntitySerializer, LinkedDataReferenceList
from mainsite.utils import OriginSetting
from recipient.models import RecipientGroup, RecipientGroupMembership, RecipientProfile
from pathway.models import Pathway


class RecipientProfileSerializer(serializers.Serializer):

    def to_representation(self, instance):
        representation = super(RecipientProfileSerializer, self).to_representation(instance)
        representation.update([
            ('@id', u"mailto:{}".format(instance.recipient_identifier)),
            ('@type', "RecipientProfile"),
            ('slug', instance.slug),
            ('name', instance.display_name),
            ('email', instance.recipient_identifier)
        ])
        return representation


class RecipientGroupMembershipSerializer(LinkedDataEntitySerializer):
    jsonld_type = "RecipientGroupMembership"

    email = serializers.EmailField(write_only=True, source='recipient_identifier')
    name = serializers.CharField(source='membership_name')
    slug = serializers.CharField(source='recipient_profile.slug', read_only=True)

    def to_representation(self, instance):
        json = super(RecipientGroupMembershipSerializer, self).to_representation(instance)
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
            ("@context", OriginSetting.HTTP+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupMembershipList"),
            ("recipientGroup", OriginSetting.JSON+reverse('recipient_group_detail', kwargs={'issuer_slug': issuer_slug, 'group_slug': recipient_group_slug})),
            ("memberships", members_serializer.data),
        ])


class RecipientGroupSerializer(LinkedDataEntitySerializer):
    jsonld_type = "RecipientGroup"

    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    slug = serializers.CharField(read_only=True)
    active = serializers.BooleanField(source='is_active', default=True)
    issuer = LinkedDataReferenceField(keys=['slug'], model=Issuer)
    member_count = serializers.IntegerField(read_only=True)
    members = RecipientGroupMembershipSerializer(
        read_only=False, many=True, required=False, source='cached_members'
    )
    pathways = LinkedDataReferenceList(
        read_only=False, required=False, source='cached_pathways',
        child=LinkedDataReferenceField(read_only=False, keys=['slug'], model=Pathway)
    )

    def to_representation(self, instance):
        if not self.context.get('embedRecipients', False) and 'members' in self.fields:
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

            for p in pathways_to_add:
                instance.pathways.add(p)

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

class RecipientGroupListSerializer(serializers.Serializer):
    def to_representation(self, recipient_groups):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        groups_serializer = RecipientGroupSerializer(recipient_groups, many=True, context=self.context)
        return OrderedDict([
            ("@context", OriginSetting.HTTP+"/public/context/pathways"),
            ("@type", "IssuerRecipientGroupList"),
            ("issuer", OriginSetting.JSON+reverse('issuer_json', kwargs={'slug': issuer_slug})),
            ("recipientGroups", groups_serializer.data)
        ])
