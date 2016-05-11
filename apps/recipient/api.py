# Created by wiggins@concentricsky.com on 3/31/16.
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response

from issuer.api import AbstractIssuerAPIEndpoint
from issuer.models import Issuer
from recipient.models import RecipientGroup, RecipientProfile, RecipientGroupMembership
from recipient.serializers import RecipientGroupSerializer, RecipientGroupListSerializer, RecipientProfileSerializer, \
    RecipientGroupMembershipListSerializer, RecipientGroupMembershipSerializer

_TRUE_VALUES = ['true','t','on','yes','y','1',1,1.0,True]
_FALSE_VALUES = ['false','f','off','no','n','0',0,0.0,False]


def _scrub_boolean(boolean_str, default=None):
    if boolean_str in _TRUE_VALUES:
        return True
    if boolean_str in _FALSE_VALUES:
        return False
    return default


class RecipientGroupList(AbstractIssuerAPIEndpoint):

    def get(self, request, issuer_slug):
        """
        GET a list of Recipient Groups owned by an Issuer
        ---
        serializer: RecipientGroupSerializer
        parameters:
            - name: embedRecipients
              description: Whether or not to include Recipient Profiles information
              required: false
              default: false
              type: boolean
              paramType: query
        """

        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            self.check_object_permissions(self.request, issuer)
        except PermissionDenied:
            return Response(status=status.HTTP_404_NOT_FOUND)

        embed_recipients = _scrub_boolean(request.query_params.get('embedRecipients', False))

        groups = issuer.cached_recipient_groups()
        serializer = RecipientGroupListSerializer(groups, context={
            'request': request,
            'embedRecipients': embed_recipients,
            'issuer_slug': issuer_slug,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug):
        """
        Define a new Recipient Group
        ---
        serializer: RecipientGroupSerializer
        parameters:
            - name: name
              description: The name of the new Recipient Group
              required: true
              type: string
              paramType: form
            - name: description
              description: A short description of the new Recipient Group
              required: false
              type: string
              paramType: form
        """
        serializer = RecipientGroupSerializer(data=request.data, context={
            'request': request,
            'embedRecipients': True,
            'issuer_slug': issuer_slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        recipient_group = serializer.data

        # TODO: logger.event(badgrlog.RecipientGroupCreatedEvent(recipient_group))
        return Response(recipient_group, status=status.HTTP_201_CREATED)


class RecipientGroupAPIEndpoint(AbstractIssuerAPIEndpoint):
    def _get_issuer_and_group(self, issuer_slug, group_slug):
        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return None, None
        try:
            self.check_object_permissions(self.request, issuer)
        except PermissionDenied:
            return None, None

        try:
            recipient_group = RecipientGroup.cached.get(slug=group_slug)
        except RecipientGroup.DoesNotExist:
            return issuer, None

        if recipient_group.issuer != issuer:
            return issuer, None

        return issuer, recipient_group


class RecipientGroupDetail(RecipientGroupAPIEndpoint):

    def get(self, request, issuer_slug, group_slug):
        """
        GET detailed information about a Recipient Group
        ---
        serializer: RecipientGroupSerializer
        parameters:
            - name: embedRecipients
              description: Whether or not to include Recipient Profiles information
              required: false
              default: false
              type: boolean
              paramType: query
        """
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        embed_recipients = _scrub_boolean(request.query_params.get('embedRecipients', False))

        serializer = RecipientGroupSerializer(recipient_group, context={
            'request': request,
            'embedRecipients': embed_recipients,
            'issuer_slug': issuer_slug
        })
        return Response(serializer.data)

    def delete(self, request, issuer_slug, group_slug):
        """
        DELETE a Recipient Group
        ---
        """
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        # logger.event(badgrlog.RecipientGroupDeletedEvent(recipient_group))
        old_name = unicode(recipient_group)
        recipient_group.delete()
        return Response(u"Recipient Group '{}' was removed.".format(old_name), status=status.HTTP_200_OK)

    def put(self, request, issuer_slug, group_slug):
        """
        Update an existing Recipient Group
        ---
        parameters:
            - name: name
              description: The name of the new Recipient Group
              required: true
              type: string
              paramType: form
            - name: description
              description: A short description of the new Recipient Group
              required: false
              type: string
              paramType: form
            - name: active
              required: false
              type: boolean
              paramType: form
        """

        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = RecipientGroupSerializer(recipient_group, data=request.data, context={
            'request': request,
            'embedRecipients': False,
            'issuer_slug': issuer_slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class RecipientGroupMembershipList(RecipientGroupAPIEndpoint):
    def get(self, request, issuer_slug, group_slug):
        """
        GET the list of Recipients in a Recipient Group
        ---
        serializer: RecipientProfileSerializer
        """
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = RecipientGroupMembershipListSerializer(recipient_group.cached_members(), context={
            'request': request,
            'issuer_slug': issuer_slug,
            'recipient_group_slug': group_slug,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug, group_slug):
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

        serializer = RecipientGroupMembershipSerializer(membership, context={
            'request': request,
        })
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RecipientGroupMembershipDetail(RecipientGroupAPIEndpoint):
    def put(self, request, issuer_slug, group_slug, membership_slug):
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
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            membership = RecipientGroupMembership.cached.get(slug=membership_slug)
        except RecipientGroupMembership.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if membership.recipient_group != recipient_group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        membership.membership_name = request.data.get('name')
        membership.save()
        serializer = RecipientGroupMembershipSerializer(membership, context={
            'request': request
        })
        return Response(serializer.data)

    def delete(self, request, issuer_slug, group_slug, membership_slug):
        """
        Remove a Recipient from a Recipient Group
        ---
        """
        issuer, recipient_group = self._get_issuer_and_group(issuer_slug, group_slug)
        if issuer is None or recipient_group is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            membership = RecipientGroupMembership.cached.get(slug=membership_slug)
        except RecipientGroupMembership.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if membership.recipient_group != recipient_group:
            return Response(status=status.HTTP_404_NOT_FOUND)

        membership.delete()
        return Response(status=status.HTTP_200_OK)
