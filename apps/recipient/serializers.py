# Created by wiggins@concentricsky.com on 3/31/16.
from django.conf import settings
from django.core.urlresolvers import reverse
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer
from recipient.models import RecipientGroup


class RecipientProfileSerializer(serializers.Serializer):

    def to_representation(self, instance):
        representation = super(RecipientProfileSerializer, self).to_representation(instance)
        representation.update({
            '@id': u"mailto:{}".format(instance.recipient_identifier),
            '@type': "RecipientProfile",
            'name': instance.display_name,
        })
        return representation


class RecipientGroupMembershipSerializer(serializers.Serializer):
    def to_representation(self, instance):
        representation = super(RecipientGroupMembershipSerializer, self).to_representation(instance)
        representation.update({
            '@id': u"mailto:{}".format(instance.recipient_profile.recipient_identifier),
            '@type': "RecipientProfile",
            'name': instance.membership_name,
            'pk': instance.pk,
        })
        return representation


class RecipientGroupSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)

    def to_representation(self, instance):
        embed_recipients = self.context.get('embedRecipients', False)

        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("No issuer")

        representation = super(RecipientGroupSerializer, self).to_representation(instance)
        representation.update({
            '@id': settings.HTTP_ORIGIN+reverse('recipient_group_detail', kwargs={'issuer_slug': issuer_slug, 'pk': instance.pk}),
            '@type': "RecipientGroup",
            'pk': instance.pk
        })
        members_serializer = RecipientGroupMembershipSerializer(instance.cached_members(), many=True, context=self.context)
        if embed_recipients:
            representation['members'] = members_serializer.data
        return representation

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


class RecipientGroupListSerializer(serializers.Serializer):

    def to_representation(self, recipient_groups):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        groups_serializer = RecipientGroupSerializer(recipient_groups, many=True, context=self.context)
        return {
            "@context": settings.HTTP_ORIGIN+"/public/context/pathways",
            "@type": "IssuerRecipientGroupList",
            "issuer": settings.HTTP_ORIGIN+reverse('issuer_json', kwargs={'slug': issuer_slug}),
            "recipientGroups": groups_serializer.data
        }


class RecipientGroupMembershipListSerializer(serializers.Serializer):
    def to_representation(self, memberships):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        recipient_group_pk = self.context.get('recipient_group_pk', None)
        if not recipient_group_pk:
            raise ValidationError("Invalid recipient_group_pk")

        members_serializer = RecipientGroupMembershipSerializer(memberships, many=True, context=self.context)
        return {
            "@context": settings.HTTP_ORIGIN+"/public/context/pathways",
            "@type": "IssuerRecipientGroupMembershipList",
            "recipientGroup": settings.HTTP_ORIGIN+reverse('recipient_group_detail', kwargs={'issuer_slug': issuer_slug, 'group_pk': recipient_group_pk}),
            "memberships": members_serializer.data
        }
