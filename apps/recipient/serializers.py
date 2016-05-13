# Created by wiggins@concentricsky.com on 3/31/16.
from collections import OrderedDict

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from mainsite.serializers import LinkedDataReferenceField, LinkedDataEntitySerializer
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
        ])
        return representation


class RecipientGroupMembershipSerializer(LinkedDataEntitySerializer):
    jsonld_type = 'RecipientGroupMembership'

    name = serializers.CharField(source='membership_name')
    email = serializers.CharField(source='recipient_identifier')
    slug = serializers.CharField(read_only=True)



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
    active = serializers.BooleanField(source='is_active', default=True)
    issuer = LinkedDataReferenceField(['slug'], Issuer)
    member_count = serializers.IntegerField(read_only=True)
    members = RecipientGroupMembershipSerializer(many=True, source='cached_members', required=False)
    pathways = LinkedDataReferenceField(['slug'], Pathway, many=True, required=False)

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

        if 'pathways' in validated_data:
            existing_pathway_ids = set(instance.cached_pathways())
            updated_pathway_ids = set(validated_data.get('pathways'))

            pathways_to_delete = existing_pathway_ids - updated_pathway_ids
            pathways_to_add = updated_pathway_ids - existing_pathway_ids

            for p in pathways_to_delete:
                instance.pathways.remove(p)

            for p in pathways_to_add:
                instance.pathways.add(p)

        if 'cached_members' in validated_data:
            api_members = validated_data.get('cached_members')

            api_members_by_email = dict((m[u'recipient_identifier'], m) for m in api_members)

            existing_member_emails = set([m.recipient_profile.recipient_identifier for m in instance.cached_members()])
            updated_member_emails = set([m[u'recipient_identifier'] for m in api_members])

            members_to_delete = existing_member_emails - updated_member_emails

            for member_email in members_to_delete:
                profile = RecipientProfile.cached.get(recipient_identifier=member_email)
                membership = RecipientGroupMembership.cached.get(recipient_group=instance, recipient_profile=profile)
                membership.delete()

            for member in api_members:
                member_name = member[u'membership_name']
                member_email = member[u'recipient_identifier']

                try:
                    profile = RecipientProfile.objects.get(recipient_identifier=member_email)
                except ObjectDoesNotExist:
                    profile = RecipientProfile(
                        recipient_identifier=member_email,
                        display_name=member_name
                    )
                    profile.save()

                try:
                    membership = RecipientGroupMembership.objects.get(recipient_group=instance, recipient_profile=profile)
                except ObjectDoesNotExist:
                    membership = RecipientGroupMembership(
                        recipient_group=instance,
                        recipient_profile=profile,
                        membership_name=member_name
                    )
                    membership.save()

                if membership.membership_name != member_name:
                    membership.membership_name = member_name
                    membership.save()


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
