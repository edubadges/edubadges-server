from collections import OrderedDict

import datetime, copy

import dateutil.parser, json
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from django.shortcuts import get_object_or_404
from oauth2_provider.models import AccessToken
from oauthlib.oauth2.rfc6749.tokens import random_token_generator
from rest_framework import status, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN

import badgrlog
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin, BaseEntityView, \
    UncachedPaginatedViewMixin
from entity.serializers import BaseSerializerV2, V2ErrorSerializer
from issuer.utils import mapExtensionsToDict
from issuer.models import Issuer, BadgeClass, BadgeInstance, IssuerStaff
from issuer.permissions import (MayIssueBadgeClass, MayEditBadgeClass,
                                IsEditor, IsStaff, ApprovedIssuersOnly, BadgrOAuthTokenHasScope,
                                BadgrOAuthTokenHasEntityScope)
from issuer.serializers_v1 import (IssuerSerializerV1, BadgeClassSerializerV1,
                                   BadgeInstanceSerializerV1)
from issuer.serializers_v2 import IssuerSerializerV2, BadgeClassSerializerV2, BadgeInstanceSerializerV2, \
    IssuerAccessTokenSerializerV2
from apispec_drf.decorators import apispec_get_operation, apispec_put_operation, \
    apispec_delete_operation, apispec_list_operation, apispec_post_operation
from lti_edu.models import StudentsEnrolled
from mainsite.pagination import EncryptedCursorPagination
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.serializers import CursorPaginatedListSerializer

logger = badgrlog.BadgrLogger()


class IssuerList(BaseEntityListView):
    """
    Issuer list resource for the authenticated user
    """
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    v2_serializer_class = IssuerSerializerV2
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, ApprovedIssuersOnly, BadgrOAuthTokenHasScope)
    valid_scopes = ["rw:issuer"]

    create_event = badgrlog.IssuerCreatedEvent

    def get_objects(self, request, **kwargs):
#         return self.request.user.cached_issuers()
        return self.request.user.cached_issuers_within_scope()

    @apispec_list_operation('Issuer',
        summary="Get a list of Issuers for authenticated user",
        tags=["Issuers"],
    )
    def get(self, request, **kwargs):
        return super(IssuerList, self).get(request, **kwargs)

    @apispec_post_operation('Issuer',
        summary="Create a new Issuer",
        tags=["Issuers"],
    )
    def post(self, request, **kwargs):
        if request.data['faculty']:
            request.data[u'faculty'] = json.loads(request.data[u'faculty'])
        else:
            request.data[u'faculty'] = None
        mapExtensionsToDict(request)
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

    @apispec_put_operation('Issuer',
       summary="Update a single Issuer",
       tags=["Issuers"],
   )
    def put(self, request, **kwargs):
        if request.data['faculty']:
            request.data[u'faculty'] = json.loads(request.data[u'faculty'])
        else:
             request.data[u'faculty'] = None
        mapExtensionsToDict(request)
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
    valid_scopes = ["rw:issuer"]

    def get_objects(self, request, **kwargs):
        return request.user.cached_badgeclasses()

    @apispec_list_operation('BadgeClass',
        summary="Get a list of BadgeClasses for authenticated user",
        tags=["BadgeClasses"],
    )
    def get(self, request, **kwargs):
        return super(AllBadgeClassesList, self).get(request, **kwargs)

    @apispec_post_operation('BadgeClass',
        summary="Create a new BadgeClass",
        tags=["BadgeClasses"],
    )
    def post(self, request, **kwargs):
        mapExtensionsToDict(request)
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

    @apispec_post_operation('BadgeClass',
        summary="Create a new BadgeClass associated with an Issuer",
        description="Authenticated user must have owner, editor, or staff status on the Issuer",
        tags=["Issuers", "BadgeClasses"],
    )
    def post(self, request, **kwargs):
        issuer = self.get_object(request, **kwargs)  # trigger a has_object_permissions() check
        mapExtensionsToDict(request)
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

    valid_scopes = ["rw:issuer", "rw:issuer:*"]

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

    @apispec_put_operation('BadgeClass',
        summary='Update an existing BadgeClass.  Previously issued BadgeInstances will NOT be updated',
        tags=['BadgeClasses'],
    )
    def put(self, request, **kwargs):
        mapExtensionsToDict(request)
        return super(BadgeClassDetail, self).put(request, **kwargs)


class BatchAssertionsIssue(VersionedObjectMixin, BaseEntityView):
    model = BadgeClass  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

    def get_context_data(self, **kwargs):
        context = super(BatchAssertionsIssue, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    @apispec_post_operation('Assertion',
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

        try:
            create_notification = request.data.get('create_notification', False)
        except AttributeError:
            return Response(status=HTTP_400_BAD_REQUEST)

        # update passed in assertions to include create_notification
        def _include_create_notification(a):
            a['create_notification'] = create_notification
            return a
        assertions = map(_include_create_notification, request.data.get('assertions'))

        # save serializers
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(many=True, data=assertions, context=context)
        if not serializer.is_valid(raise_exception=False):
            serializer = V2ErrorSerializer(instance={},
                                           success=False,
                                           description="bad request",
                                           field_errors=serializer._errors,
                                           validation_errors=[])
            return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
        new_instances = serializer.save(created_by=request.user)
        for new_instance in new_instances:
            self.log_create(new_instance)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BatchAssertionsRevoke(VersionedObjectMixin, BaseEntityView):
    model = BadgeInstance
    permission_classes = (AuthenticatedWithVerifiedEmail, BadgrOAuthTokenHasEntityScope)
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

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

    @apispec_post_operation('Assertion',
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


class BadgeInstanceList(UncachedPaginatedViewMixin, VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of assertions for a single badgeclass
    POST to issue a new assertion
    """
    model = BadgeClass  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

    def get_queryset(self, request=None, **kwargs):
        badgeclass = self.get_object(request, **kwargs)
        queryset = BadgeInstance.objects.filter(
            badgeclass=badgeclass,
            revoked=False
        )

        if 'recipient' in request.query_params:
            recipient_id = request.query_params.get('recipient').lower()
            queryset = queryset.filter(recipient_identifier=recipient_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super(BadgeInstanceList, self).get_context_data(**kwargs)
        context['badgeclass'] = self.get_object(self.request, **kwargs)
        return context

    @apispec_list_operation('Assertion',
        summary="Get a list of Assertions for a single BadgeClass",
        tags=['Assertions', 'BadgeClasses'],
        parameters=[
            {
                'in': 'query',
                'name': "recipient",
                'type': "string",
                'description': 'A recipient identifier to filter by'
            },
            {
                'in': 'query',
                'name': "num",
                'type': "string",
                'description': 'Request pagination of results'
            }
        ]
    )
    def get(self, request, **kwargs):
        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)

        return super(BadgeInstanceList, self).get(request, **kwargs)

    @apispec_post_operation('Assertion',
        summary="Issue an Assertion to a single recipient",
        tags=['Assertions', 'BadgeClasses'],
    )
    def post(self, request, **kwargs):
        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)
        recipients = request.data.pop('recipients')
        for recipient in recipients:
            if recipient['selected']:
                request.data['recipientprofile_name'] = recipient['recipient_name']
                request.data['recipient_type'] = recipient['recipient_type']
                request.data['recipient_identifier'] = recipient['recipient_identifier']
                response = super(BadgeInstanceList, self).post(request, **kwargs) 
                if response.status_code == 201:
                    badge_class = get_object_or_404(BadgeClass, entity_id=request.data.get('badge_class', -1))
                    StudentsEnrolled.objects \
                        .filter(badge_class=badge_class, edu_id=recipient['recipient_identifier']) \
                        .update(date_awarded=timezone.now(), assertion_slug=response.data.get('slug'))
        return response


class IssuerBadgeInstanceList(UncachedPaginatedViewMixin, VersionedObjectMixin, BaseEntityListView):
    """
    Retrieve all assertions within one issuer
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsStaff, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    create_event = badgrlog.BadgeInstanceCreatedEvent
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

    def get_queryset(self, request=None, **kwargs):
        issuer = self.get_object(request, **kwargs)
        queryset = BadgeInstance.objects.filter(
            issuer=issuer,
            revoked=False
        )

        if 'recipient' in request.query_params:
            recipient_id = request.query_params.get('recipient').lower()
            queryset = queryset.filter(recipient_identifier=recipient_id)
        return queryset

    @apispec_list_operation('Assertion',
        summary='Get a list of Assertions for a single Issuer',
        tags=['Assertions', 'Issuers'],
        parameters=[
            {
                'in': 'query',
                'name': "recipient",
                'type': "string",
                'description': 'A recipient identifier to filter by'
            },
            {
                'in': 'query',
                'name': "num",
                'type': "string",
                'description': 'Request pagination of results'
            }
        ]
    )
    def get(self, request, **kwargs):
        return super(IssuerBadgeInstanceList, self).get(request, **kwargs)

    @apispec_post_operation('Assertion',
        summary="Issue a new Assertion to a recipient",
        tags=['Assertions', 'Issuers']
    )
    def post(self, request, **kwargs):
        kwargs['issuer'] = self.get_object(request, **kwargs)  # trigger a has_object_permissions() check
        return super(IssuerBadgeInstanceList, self).post(request, **kwargs)


class BadgeInstanceDetail(BaseEntityDetailView):
    """
    Endpoints for (GET)ting a single assertion or revoking a badge (DELETE)
    """
    model = BadgeInstance
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    v2_serializer_class = BadgeInstanceSerializerV2
    valid_scopes = ["rw:issuer", "rw:issuer:*"]

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

    @apispec_put_operation('Assertion',
        summary="Update an Assertion",
        tags=['Assertions'],
    )
    def put(self, request, **kwargs):
        return super(BadgeInstanceDetail, self).put(request, **kwargs)


class IssuerTokensList(BaseEntityListView):
    model = AccessToken
    permission_classes = (AuthenticatedWithVerifiedEmail, BadgrOAuthTokenHasScope)
    v2_serializer_class = IssuerAccessTokenSerializerV2
    valid_scopes = ["rw:issuer"]

    @apispec_post_operation('AccessToken',
        summary="Retrieve issuer tokens",
        tags=["Issuers"],
    )
    def post(self, request, **kwargs):
        if not isinstance(request.auth, AccessToken):
            # need to use a oauth2 bearer token to authorize
            error_response = BaseSerializerV2.response_envelope(result=[], success=False, description="Invalid token")
            return Response(error_response, status=HTTP_403_FORBIDDEN)

        issuer_entityids = request.data.get('issuers', None)
        if not issuer_entityids:
            raise serializers.ValidationError({"issuers": "field is required"})

        issuers = []
        for issuer_entityid in issuer_entityids:
            try:
                issuer = Issuer.cached.get(entity_id=issuer_entityid)
                self.check_object_permissions(request, issuer)
            except Issuer.DoesNotExist as e:
                raise serializers.ValidationError({"issuers": "unknown issuer"})
            else:
                issuers.append(issuer)

        tokens = []
        expires = timezone.now() + datetime.timedelta(weeks=5200)
        for issuer in issuers:
            scope = "rw:issuer:{}".format(issuer.entity_id)

            # grant application user staff access to issuer if needed
            staff, staff_created = IssuerStaff.cached.get_or_create(
                issuer=issuer,
                user=request.auth.application.user,
                defaults=dict(
                    role=IssuerStaff.ROLE_STAFF
                )
            )

            accesstoken, created = AccessToken.objects.get_or_create(
                user=request.auth.application.user,
                application=request.auth.application,
                scope=scope,
                defaults=dict(
                    expires=expires,
                    token=random_token_generator(request)
                )
            )
            tokens.append({
                'issuer': issuer.entity_id,
                'token': accesstoken.token,
                'expires': accesstoken.expires,
            })

        serializer = IssuerAccessTokenSerializerV2(data=tokens, many=True, context=dict(
            request=request,
            kwargs=kwargs
        ))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class PaginatedAssertionsSinceSerializer(CursorPaginatedListSerializer):
    child = BadgeInstanceSerializerV2()

    def __init__(self, *args, **kwargs):
        self.timestamp = timezone.now()  # take timestamp now before SQL query is run in super.__init__
        super(PaginatedAssertionsSinceSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, data):
        representation = super(PaginatedAssertionsSinceSerializer, self).to_representation(data)
        representation['timestamp'] = self.timestamp.isoformat()
        return representation


class AssertionsChangedSince(BaseEntityView):
    permission_classes = (BadgrOAuthTokenHasScope,)
    valid_scopes = ["r:assertions"]

    def get_user(self, request):
        if request.user:
            return request.user
        if request.auth:
            return request.auth.application.user

    def get_queryset(self, request, since=None):
        user = self.get_user(request)
        issuer_ids = [i.id for i in user.cached_issuers()]

        authorized_badgeusers = request.auth.application.accesstoken_set.all()
        user_ids = [u.id for u in authorized_badgeusers]

        # select badgeinstance.* where
        #   (
        #     badgeinstance.issuer_id in (:issuer_ids)
        #     OR
        #     backpackcollectionbadgeinstance.badgeuser_id in (:user_ids)
        #   )
        #   AND
        #   badgeinstance.updated_at >= since

        expr = Q(issuer_id__in=issuer_ids) | Q(backpackcollectionbadgeinstance__badgeuser_id__in=user_ids)

        if since is not None:
            expr &= Q(updated_at__gt=since)

        qs = BadgeInstance.objects.filter(expr)
        return qs

    def get(self, request, **kwargs):
        since = request.GET.get('since', None)
        if since is not None:
            try:
                since = dateutil.parser.parse(since)
            except ValueError as e:
                err = V2ErrorSerializer(data={}, field_errors={'since': ["must be iso8601 format"]}, validation_errors=[])
                err._success = False
                err._description = "bad request"
                err.is_valid(raise_exception=False)
                return Response(err.data, status=HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset(request, since=since)
        context = self.get_context_data(**kwargs)
        serializer = PaginatedAssertionsSinceSerializer(
            queryset=queryset,
            request=request,
            context=context)
        serializer.is_valid()
        return Response(serializer.data)

        # return super(AssertionsChangedSince, self).get(request, **kwargs)
