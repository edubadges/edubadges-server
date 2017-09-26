from collections import OrderedDict

from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK

import badgrlog
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin, BaseEntityView
from entity.serializers import BaseSerializerV2
from issuer.models import Issuer, BadgeClass, BadgeInstance
from issuer.permissions import (MayIssueBadgeClass, MayEditBadgeClass,
                                IsEditor, IsStaff, ApprovedIssuersOnly, BadgrOAuthTokenHasScope,
                                BadgrOAuthTokenHasEntityScope)
from issuer.serializers_v1 import (IssuerSerializerV1, BadgeClassSerializerV1,
                                   BadgeInstanceSerializerV1)
from issuer.serializers_v2 import IssuerSerializerV2, BadgeClassSerializerV2, BadgeInstanceSerializerV2
from mainsite.decorators import apispec_get_operation, apispec_put_operation, \
    apispec_delete_operation, apispec_list_operation, apispec_post_operation
from mainsite.permissions import AuthenticatedWithVerifiedEmail

logger = badgrlog.BadgrLogger()


class IssuerList(BaseEntityListView):
    """
    Issuer list resource for the authenticated user
    """
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    v2_serializer_class = IssuerSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, ApprovedIssuersOnly, BadgrOAuthTokenHasScope)
    valid_scopes = ["l:issuer"]

    create_event = badgrlog.IssuerCreatedEvent

    def get_objects(self, request, **kwargs):
        return self.request.user.cached_issuers()

    @apispec_list_operation('Issuer',
        summary="Get a list of Issuers for authenticated user",
        tags=["Issuers"],
    )
    def get(self, request, **kwargs):
        return super(IssuerList, self).get(request, **kwargs)

    @apispec_post_operation('Issuer', IssuerSerializerV2,
        summary="Create a new Issuer",
        tags=["Issuers"],
    )
    def post(self, request, **kwargs):
        return super(IssuerList, self).post(request, **kwargs)


class IssuerDetail(BaseEntityDetailView):
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    v2_serializer_class = IssuerSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, BadgrOAuthTokenHasEntityScope)
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

    @apispec_get_operation('Issuer',
        summary="Get a single Issuer",
        tags=["Issuers"],
    )
    def get(self, request, **kwargs):
        return super(IssuerDetail, self).get(request, **kwargs)

    @apispec_put_operation('Issuer', IssuerSerializerV2,
       summary="Update a single Issuer",
       tags=["Issuers"],
   )
    def put(self, request, **kwargs):
        return super(IssuerDetail, self).put(request, **kwargs)

    @apispec_delete_operation('Issuer',
        summary="Delete a single Issuer",
        tags=["Issuers"],
    )
    def delete(self, request, **kwargs):
        return super(IssuerDetail, self).delete(request, **kwargs)


class AllBadgeClassesList(BaseEntityListView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail, BadgrOAuthTokenHasScope)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2
    valid_scopes = ["l:badgeclass"]

    def get_objects(self, request, **kwargs):
        return request.user.cached_badgeclasses()

    @apispec_list_operation('BadgeClass',
        summary="Get a list of BadgeClasses for authenticated user",
        tags=["BadgeClasses"],
    )
    def get(self, request, **kwargs):
        return super(AllBadgeClassesList, self).get(request, **kwargs)

    @apispec_post_operation('BadgeClass', BadgeClassSerializerV2,
        summary="Create a new BadgeClass",
        tags=["BadgeClasses"],
    )
    def post(self, request, **kwargs):
        return super(AllBadgeClassesList, self).post(request, **kwargs)


class IssuerBadgeClassList(VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2
    create_event = badgrlog.BadgeClassCreatedEvent
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

    def get_objects(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)
        return issuer.cached_badgeclasses()

    def get_context_data(self, **kwargs):
        context = super(IssuerBadgeClassList, self).get_context_data(**kwargs)
        context['issuer'] = self.get_object(self.request, **kwargs)
        return context

    @apispec_list_operation('BadgeClass',
        summary="Get a list of BadgeClasses for a single Issuer",
        description="Authenticated user must have owner, editor, or staff status on the Issuer",
        tags=["Issuers", "BadgeClasses"],
    )
    def get(self, request, **kwargs):
        return super(IssuerBadgeClassList, self).get(request, **kwargs)

    @apispec_post_operation('BadgeClass', BadgeClassSerializerV2,
        summary="Create a new BadgeClass associated with an Issuer",
        description="Authenticated user must have owner, editor, or staff status on the Issuer",
        tags=["Issuers", "BadgeClasses"],
    )
    def post(self, request, **kwargs):
        return super(IssuerBadgeClassList, self).post(request, **kwargs)


class BadgeClassDetail(BaseEntityDetailView):
    """
    GET details on one BadgeClass.
    PUT and DELETE should be restricted to BadgeClasses that haven't been issued yet.
    """
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeClassSerializerV1
    v2_serializer_class = BadgeClassSerializerV2

    valid_scopes = ["rw:badgeclass", "rw:badgeclass:*"]

    @apispec_get_operation('BadgeClass',
        summary='Get a single BadgeClass',
        tags=['BadgeClasses'],
    )
    def get(self, request, **kwargs):
        return super(BadgeClassDetail, self).get(request, **kwargs)

    @apispec_delete_operation('BadgeClass',
        summary="Delete a BadgeClass",
        description="Restricted to owners or editors (not staff) of the corresponding Issuer.",
        tags=['BadgeClasses'],
        responses=OrderedDict([
            ("400", {
                'description': "BadgeClass couldn't be deleted. It may have already been issued."
            }),

        ])
    )
    def delete(self, request, **kwargs):
        # TODO: log delete methods
        # logger.event(badgrlog.BadgeClassDeletedEvent(old_badgeclass, request.user))
        return super(BadgeClassDetail, self).delete(request, **kwargs)

    @apispec_put_operation('BadgeClass', BadgeClassSerializerV2,
        summary='Update an existing BadgeClass.  Previously issued BadgeInstances will NOT be updated',
        tags=['BadgeClasses'],
    )
    def put(self, request, **kwargs):
        return super(BadgeClassDetail, self).put(request, **kwargs)


class BatchAssertionsIssue(VersionedObjectMixin, BaseEntityView):
    model = BadgeClass  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:assertion"]

    def get_context_data(self, **kwargs):
        context = super(BatchAssertionsIssue, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    @apispec_post_operation('Assertion', BadgeInstanceSerializerV2,
        summary='Issue multiple copies of the same BadgeClass to multiple recipients',
        tags=['Assertions'],
        parameters=[
            {
                "in": "body",
                "name": "body",
                "required": True,
                'schema': {
                    "type": "array",
                    'items': { '$ref': '#/definitions/Assertion' }
                },
            }
        ]
    )
    def post(self, request, **kwargs):
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


class BatchAssertionsRevoke(VersionedObjectMixin, BaseEntityView):
    model = BadgeInstance
    permission_classes = (AuthenticatedWithVerifiedEmail, BadgrOAuthTokenHasScope)
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:assertion"]

    def get_context_data(self, **kwargs):
        context = super(BatchAssertionsRevoke, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    def _process_revoke(self, request, revocation):
        response = {
            "revoked": False,
        }

        entity_id = revocation.get("entityId", None)
        revocation_reason = revocation.get("revocationReason", None)

        if entity_id is None:
            return dict(response, reason="entityId is required")

        response["entityId"] = entity_id

        if revocation_reason is None:
            return dict(response, reason="revocationReason is required")

        response["revocationReason"] = revocation_reason

        try:
            assertion = self.get_object(request, entity_id=entity_id)
        except Http404:
            return dict(response, reason="permission denied or object not found")

        if not self.has_object_permissions(request, assertion):
            dict(response, reason="permission denied or object not found")


        try:
            assertion.revoke(revocation_reason)
        except Exception as e:
            return dict(response, reason=e.message)

        return dict(response, revoked=True)

    @apispec_post_operation('Assertion', BadgeInstanceSerializerV2,
        summary='Revoke multiple Assertions',
        tags=['Assertions'],
        parameters=[
            {
                "in": "body",
                "name": "body",
                "required": True,
                'schema': {
                    "type": "array",
                    'items': { '$ref': '#/definitions/Assertion' }
                },
            }
        ]
    )
    def post(self, request, **kwargs):
        result = [
            self._process_revoke(request, revocation)
            for revocation in self.request.data
        ]

        response_data = BaseSerializerV2.response_envelope(result=result, success=True, description="revoked badges")

        return Response(status=HTTP_200_OK, data=response_data)


class BadgeInstanceList(VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of assertions for a single badgeclass
    POST to issue a new assertion
    """
    model = BadgeClass  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent
    valid_scopes = ["l:assertion"]

    def get_objects(self, request, **kwargs):
        badgeclass = self.get_object(request, **kwargs)
        return badgeclass.cached_badgeinstances()

    def get_context_data(self, **kwargs):
        context = super(BadgeInstanceList, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    @apispec_list_operation('Assertion',
        summary="Get a list of Assertions for a single BadgeClass",
        tags=['Assertions', 'BadgeClasses'],
    )
    def get(self, request, **kwargs):
        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(BadgeInstanceList, self).get(request, **kwargs)

    @apispec_post_operation('Assertion', BadgeInstanceSerializerV2,
        summary="Issue an Assertion to a single recipient",
        tags=['Assertions', 'BadgeClasses'],
    )
    def post(self, request, **kwargs):
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
    permission_classes = (AuthenticatedWithVerifiedEmail, IsStaff, BadgrOAuthTokenHasScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent
    valid_scopes = ["l:assertion"]

    def get_objects(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)
        assertions = issuer.cached_badgeinstances()

        # filter badgeclasses by recipient if present in query_params
        if 'recipient' in request.query_params:
            recipient_id = request.query_params.get('recipient').lower()
            assertions = filter(lambda a: a.recipient_identifier == recipient_id, assertions)

        return assertions

    @apispec_list_operation('Assertion',
        summary='Get a list of Assertions for a single Issuer',
        tags=['Assertions', 'Issuers']
    )
    def get(self, request, **kwargs):
        return super(IssuerBadgeInstanceList, self).get(request, **kwargs)

    @apispec_post_operation('Assertion', BadgeInstanceSerializerV2,
        summary="Issue a new Assertion to a recipient",
        tags=['Assertions', 'Issuers']
    )
    def post(self, request, **kwargs):
        return super(IssuerBadgeInstanceList, self).post(request, **kwargs)


class BadgeInstanceDetail(BaseEntityDetailView):
    """
    Endpoints for (GET)ting a single assertion or revoking a badge (DELETE)
    """
    model = BadgeInstance
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:assertion", "rw:assertion:*"]

    @apispec_get_operation('Assertion',
        summary="Get a single Assertion",
        tags=['Assertions']
    )
    def get(self, request, **kwargs):
        return super(BadgeInstanceDetail, self).get(request, **kwargs)

    @apispec_delete_operation('Assertion',
        summary="Revoke an Assertion",
        tags=['Assertions'],
        responses=OrderedDict([
            ('400', {
                'description': "Assertion is already revoked"
            })
        ])
    )
    def delete(self, request, **kwargs):
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
