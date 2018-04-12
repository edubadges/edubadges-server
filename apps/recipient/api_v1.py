# encoding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import PermissionDenied
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from issuer.api_v1 import AbstractIssuerAPIEndpoint
from issuer.models import Issuer
from recipient.models import RecipientGroup, RecipientProfile, RecipientGroupMembership
from recipient.serializers_v1 import RecipientGroupMembershipListSerializerV1, \
    RecipientGroupMembershipSerializerV1


class RecipientGroupAPIEndpoint(AbstractIssuerAPIEndpoint):
    def _get_issuer_and_group(self, issuer_slug, group_slug):
        try:
            issuer = Issuer.cached.get(entity_id=issuer_slug)
        except Issuer.DoesNotExist:
            try:
                issuer = Issuer.cached.get(slug=issuer_slug)
            except Issuer.DoesNotExist:
                return None, None
        try:
            self.check_object_permissions(self.request, issuer)
        except PermissionDenied:
            return None, None

        try:
            recipient_group = RecipientGroup.cached.get(entity_id=group_slug)
        except RecipientGroup.DoesNotExist:
            try:
                recipient_group = RecipientGroup.cached.get(slug=group_slug)
            except RecipientGroup.DoesNotExist:
                return issuer, None

        if recipient_group.issuer != issuer:
            return issuer, None

        return issuer, recipient_group


class RecipientGroupMembershipList(RecipientGroupAPIEndpoint):
    def get(self, request, **kwargs):
        """
        GET the list of Recipients in a Recipient Group
        ---
        serializer: RecipientProfileSerializer
        """
        issuer_slug = kwargs.get('issuer_slug')
        group_slug = kwargs.get('group_slug')
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RecipientGroupMembershipListSerializerV1(recipient_group.cached_members(), context={
            'request': request,
            'issuer_slug': issuer_slug,
            'recipient_group_slug': group_slug,
        })
        return Response(serializer.data)

    def post(self, request, **kwargs):
        """
        Add a recipient to a Recipient Group
        ---
        parameters:
            - name: recipient
              description: URL-encoded email address of the Recipient
              type: string
              required: true
              paramType: form
            - name: name
              description: The displayable name of the Recipient
              type: string
              required: true
              paramType: form
        """
        issuer_slug = kwargs.get('issuer_slug')
        group_slug = kwargs.get('group_slug')
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        recipient_identifier = request.data.get('recipient')
        name = request.data.get('name')

        profile, created = RecipientProfile.cached.get_or_create(recipient_identifier=recipient_identifier)
        if created:
            profile.display_name = name
            profile.save()

        membership, created = RecipientGroupMembership.cached.get_or_create(
            recipient_group=recipient_group,
            recipient_profile=profile,
        )
        membership.membership_name = name
        membership.save()

        serializer = RecipientGroupMembershipSerializerV1(membership, context={
            'request': request,
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipientGroupMembershipDetail(RecipientGroupAPIEndpoint):
    def put(self, request, **kwargs):
        """
        Update an existing Recipient Group Membership
        ---
        serializer: RecipientGroupMembershipSerializer
        parameters:
            - name: name
              description: The displayable name of the Recipient
              type: string
              required: true
              paramType: form
        """
        issuer_slug = kwargs.get('issuer_slug')
        group_slug = kwargs.get('group_slug')
        membership_slug = kwargs.get('membership_slug')
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            membership = RecipientGroupMembership.cached.get(entity_id=membership_slug)
        except RecipientGroupMembership.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if membership.recipient_group != recipient_group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        membership.membership_name = request.data.get('name')
        membership.save()
        serializer = RecipientGroupMembershipSerializerV1(membership, context={
            'request': request
        })
        return Response(serializer.data)

    def delete(self, request, **kwargs):
        """
        Remove a Recipient from a Recipient Group
        ---
        """
        issuer_slug = kwargs.get('issuer_slug')
        group_slug = kwargs.get('group_slug')
        membership_slug = kwargs.get('membership_slug')
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            membership = RecipientGroupMembership.cached.get(entity_id=membership_slug)
        except RecipientGroupMembership.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if membership.recipient_group != recipient_group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        membership.delete()
        return Response(status=status.HTTP_200_OK)
