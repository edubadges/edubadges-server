from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK

import badgrlog
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin, BaseEntityView
from issuer.models import Issuer, BadgeClass, BadgeInstance
from issuer.permissions import (MayIssueBadgeClass, MayEditBadgeClass,
                                IsEditor, IsStaff, ApprovedIssuersOnly)
from issuer.serializers_v1 import (IssuerSerializerV1, BadgeClassSerializerV1,
                                   BadgeInstanceSerializerV1)
from issuer.serializers_v2 import IssuerSerializerV2, BadgeClassSerializerV2, BadgeInstanceSerializerV2
from mainsite.permissions import AuthenticatedWithVerifiedEmail

logger = badgrlog.BadgrLogger()


class IssuerList(BaseEntityListView):
    """
    Issuer list resource for the authenticated user
    """
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    v2_serializer_class = IssuerSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, ApprovedIssuersOnly)

    create_event = badgrlog.IssuerCreatedEvent

    def get_objects(self, request, **kwargs):
        return self.request.user.cached_issuers()


class IssuerDetail(BaseEntityDetailView):
    """
    GET details on one issuer.
    """
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    v2_serializer_class = IssuerSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor)


class AllBadgeClassesList(BaseEntityListView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2

    def get_objects(self, request, **kwargs):
        return request.user.cached_badgeclasses()

    def get(self, request, **kwargs):
        """
        GET a list of badgeclasses the user has access to
        """
        return super(AllBadgeClassesList, self).get(request, **kwargs)


class IssuerBadgeClassList(VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2
    create_event = badgrlog.BadgeClassCreatedEvent

    def get_objects(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)
        return issuer.cached_badgeclasses()

    def get_context_data(self, **kwargs):
        context = super(IssuerBadgeClassList, self).get_context_data(**kwargs)
        context['issuer'] = self.get_object(self.request, **kwargs)
        return context

    def get(self, request, **kwargs):
        """
        GET a list of badgeclasses within one Issuer context.
        Authenticated user must have owner, editor, or staff status on Issuer
        """

        # verify the user has permission to the issuer
        issuer = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, issuer):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(IssuerBadgeClassList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        """
        Define a new BadgeClass to be owned by a particular Issuer.
        Authenticated user must have owner or editor status on Issuer
        """

        # verify the user has permission to the issuer
        issuer = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, issuer):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(IssuerBadgeClassList, self).post(request, **kwargs)


class BadgeClassDetail(BaseEntityDetailView):
    """
    GET details on one BadgeClass. PUT and DELETE should be restricted to BadgeClasses that haven't been issued yet.
    """
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass,)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2

    def get(self, request, **kwargs):
        """
        GET single BadgeClass representation
        """
        return super(BadgeClassDetail, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        """
        DELETE a badge class that has never been issued. This will fail if any assertions exist for the BadgeClass.
        Restricted to owners or editors (not staff) of the corresponding Issuer.
        ---
        responseMessages:
            - code: 400
              message: Badge Class either couldn't be deleted. It may have already been issued, or it may already not exist.
            - code: 200
              message: Badge has been deleted.
        """

        # TODO: log delete methods
        # logger.event(badgrlog.BadgeClassDeletedEvent(old_badgeclass, request.user))
        return super(BadgeClassDetail, self).delete(request, **kwargs)

    def put(self, request, **kwargs):
        """
        Update an existing badge class. Existing BadgeInstances will NOT be updated.
        """
        return super(BadgeClassDetail, self).put(request, **kwargs)


class BatchAssertions(VersionedObjectMixin, BaseEntityView):
    model = BadgeClass  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass,)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2

    def get_context_data(self, **kwargs):
        context = super(BatchAssertions, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    def post(self, request, **kwargs):
        """
        POST to issue multiple copies of the same badge to multiple recipients
        ---
        parameters:
            - name: assertions
              required: true
              type: array
              items: {
                serializer: BadgeInstanceSerializer
              }
              paramType: form
              description: a list of assertions to issue
        """

        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)

        create_notification = request.data.get('create_notification', False)
        def _include_create_notification(a):
            a['create_notification'] = create_notification
            return a
        # update passed in assertions to include create_notification
        assertions = map(_include_create_notification, request.data.get('assertions'))

        # save serializers
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(many=True, data=assertions, context=context)
        serializer.is_valid(raise_exception=True)
        new_instances = serializer.save(created_by=request.user)
        for new_instance in new_instances:
            self.log_create(new_instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BadgeInstanceList(VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of assertions for a single badgeclass
    POST to issue a new assertion
    """
    model = BadgeClass  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass,)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent

    def get_objects(self, request, **kwargs):
        badgeclass = self.get_object(request, **kwargs)
        return badgeclass.cached_badgeinstances()

    def get_context_data(self, **kwargs):
        context = super(BadgeInstanceList, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    def get(self, request, **kwargs):
        """
        Get a list of all issued assertions for a single BadgeClass.
        """

        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(BadgeInstanceList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        """
        Issue a badge to a single recipient.
        """

        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(BadgeInstanceList, self).post(request, **kwargs)


class IssuerBadgeInstanceList(VersionedObjectMixin, BaseEntityListView):
    """
    Retrieve all assertions within one issuer
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsStaff,)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent

    def get_objects(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)
        assertions = issuer.cached_badgeinstances()

        # filter badgeclasses by recipient if present in query_params
        if 'recipient' in request.query_params:
            recipient_id = request.query_params.get('recipient').lower()
            assertions = filter(lambda a: a.recipient_identifier == recipient_id, assertions)

        return assertions

    def get(self, request, **kwargs):
        """
        Get a list of assertions issued one issuer.
        """

        # verify the user has permission to the issuer
        issuer = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, issuer):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(IssuerBadgeInstanceList, self).get(request, **kwargs)

    def post(self, request, **kwargs):
        """
        Issue a new Assertion to a recipient
        """

        # verify the user has permission to the issuer
        issuer = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, issuer):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(IssuerBadgeInstanceList, self).post(request, **kwargs)


class BadgeInstanceDetail(BaseEntityDetailView):
    """
    Endpoints for (GET)ting a single assertion or revoking a badge (DELETE)
    """
    model = BadgeInstance
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass,)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2

    def get(self, request, **kwargs):
        """
        GET a single assertion's details.
        """
        return super(BadgeInstanceDetail, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        """
        Revoke an issued badge assertion.
        Limited to Issuer owner and editors (not staff)
        ---
        responseMessages:
            - code: 200
              message: Assertion has been revoked.
            - code: 400
              message: Assertion is already revoked
            - code: 404
              message: Assertion not found or user has inadequate permissions.
        """

        # verify the user has permission to the assertion
        assertion = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, assertion):
            return Response(status=HTTP_404_NOT_FOUND)

        revocation_reason = request.data.get('revocation_reason', None)
        if not revocation_reason:
            raise ValidationError({'revocation_reason': "This field is required"})

        assertion.revoke(revocation_reason)

        # logger.event(badgrlog.BadgeAssertionRevokedEvent(current_assertion, request.user))
        return Response(status=HTTP_200_OK)
