import datetime
from collections import OrderedDict

import badgrlog
# import dateutil.parser
from apispec_drf.decorators import apispec_get_operation, apispec_put_operation, \
    apispec_delete_operation, apispec_list_operation, apispec_post_operation
from badgeuser.permissions import BadgeUserHasSurfconextSocialAccount
# from django.db.models import Q
from django.http import Http404
# from django.utils import timezone
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin, BaseEntityView, \
    UncachedPaginatedViewMixin
from entity.serializers import BaseSerializerV2, V2ErrorSerializer
from issuer.models import Issuer, BadgeClass, BadgeInstance, IssuerStaff
from issuer.permissions import (MayIssueBadgeClass, MayEditBadgeClass,
                                IsEditor, IsStaff, ApprovedIssuersOnly, BadgrOAuthTokenHasScope,
                                BadgrOAuthTokenHasEntityScope)
from issuer.serializers_v1 import (IssuerSerializerV1, BadgeClassSerializerV1,
                                   BadgeInstanceSerializerV1)
# from issuer.serializers_v2 import IssuerSerializerV2, BadgeClassSerializerV2, BadgeInstanceSerializerV2, \
#     IssuerAccessTokenSerializerV2
from issuer.utils import mapExtensionsToDict
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from rest_framework import status #, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_400_BAD_REQUEST # , HTTP_403_FORBIDDEN
from signing import tsob
from signing.models import AssertionTimeStamp
from signing.permissions import MaySignAssertions
from staff.permissions import HasObjectPermission

logger = badgrlog.BadgrLogger()


# class IssuerList(BaseEntityListView):
#     """
#     GET a list of all readable Issuers
#     POST to create a new Issuer
#     """
#     model = Issuer
#     v1_serializer_class = IssuerSerializerV1
#     permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, ApprovedIssuersOnly, BadgrOAuthTokenHasScope, BadgeUserHasSurfconextSocialAccount)
#     valid_scopes = ["rw:issuer"]
#
#     create_event = badgrlog.IssuerCreatedEvent
#
#     def get_objects(self, request, **kwargs):
#         return self.request.user.get_issuers(['read'])
#
#     @apispec_list_operation('Issuer',
#         summary="Get a list of Issuers for authenticated user",
#         tags=["Issuers"],
#     )
#     def get(self, request, **kwargs):
#         return super(IssuerList, self).get(request, **kwargs)
#
#     @apispec_post_operation('Issuer',
#         summary="Create a new Issuer",
#         tags=["Issuers"],
#     )
#     def post(self, request, **kwargs):
#         return super(IssuerList, self).post(request, **kwargs)


class IssuerDetail(BaseEntityDetailView):
    model = Issuer
    v1_serializer_class = IssuerSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, IsEditor, BadgrOAuthTokenHasEntityScope, BadgeUserHasSurfconextSocialAccount)
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
        mapExtensionsToDict(request)
        return super(IssuerDetail, self).put(request, **kwargs)

    @apispec_delete_operation('Issuer',
        summary="Delete a single Issuer",
        tags=["Issuers"],
    )
    def delete(self, request, **kwargs):
        return super(IssuerDetail, self).delete(request, **kwargs)


# class AllBadgeClassesList(BaseEntityListView):
#     """
#     GET a list of all readable badgeclasses
#     """
#     model = BadgeClass
#     allowed_methods = ('GET',)
#     permission_classes = (AuthenticatedWithVerifiedEmail, BadgrOAuthTokenHasScope)
#     v1_serializer_class = BadgeClassSerializerV1
#     valid_scopes = ["rw:issuer"]
#
#     def get_objects(self, request, **kwargs):
#         return request.user.get_badgeclasses(['read'])
#
#     @apispec_list_operation('BadgeClass',
#         summary="Get a list of BadgeClasses for authenticated user",
#         tags=["BadgeClasses"],
#     )
#     def get(self, request, **kwargs):
#         return super(AllBadgeClassesList, self).get(request, **kwargs)
#
#     # @apispec_post_operation('BadgeClass',
#     #     summary="Create a new BadgeClass",
#     #     tags=["BadgeClasses"],
#     # )
#     # def post(self, request, **kwargs):
#     #     return super(AllBadgeClassesList, self).post(request, **kwargs)


class IssuerBadgeClassList(VersionedObjectMixin, BaseEntityListView):
    """
    GET a list of badgeclasses within one issuer context or
    POST to create a new badgeclass within the issuer context
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = BadgeClassSerializerV1
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
        return super(IssuerBadgeClassList, self).post(request, **kwargs)


class BadgeClassDetail(BaseEntityDetailView):
    """
    GET details on one BadgeClass.
    PUT and DELETE should be restricted to BadgeClasses that haven't been issued yet.
    """
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail, MayEditBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeClassSerializerV1

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
        return super(BadgeClassDetail, self).put(request, **kwargs)


class TimestampedBadgeInstanceList(BaseEntityListView):
    allowed_methods = ('GET', 'DELETE')
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)
    serializer_class = BadgeInstanceSerializerV1

    def get(self, request, **kwargs):
        return super(TimestampedBadgeInstanceList, self).get(request, **kwargs)

    def get_objects(self, request, **kwargs):
        return request.user.get_assertions_ready_for_signing()

    def delete(self, request, **kwargs):
        badge_instance_slug = request.data.get('badge_instance_slug')
        badge_instance = BadgeInstance.objects.get(entity_id=badge_instance_slug)
        assertion_timestamp = AssertionTimeStamp.objects.get(badge_instance=badge_instance)
        if assertion_timestamp.signer != request.user:
            raise ValidationError('You can only delete your own timestamped badges.')
        badge_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BatchSignAssertions(BaseEntityListView):
    allowed_methods = ('POST',)
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)
    serializer_class = BadgeInstanceSerializerV1

    def post(self, request, **kwargs):
        # post assertions to be signed
        password = request.data.get('password')
        assertion_slugs = [instance['slug'] for instance in request.data.get('badge_instances')]
        user = request.user
        if not password:
            raise ValidationError('Cannot sign badges: no password provided.')
        if not assertion_slugs:
            raise ValidationError('No badges to sign.')
        if not user.may_sign_assertions:
            raise ValidationError('You do not have permission to sign badges.')
        assertion_instances = []
        batch_of_assertion_json = []
        for ass_slug in assertion_slugs:  # pun intended
            assertion_instance = BadgeInstance.objects.get(entity_id=ass_slug)
            if not user in [staff.user for staff in assertion_instance.issuer.current_signers]:
                raise ValidationError('You are not a signer for this issuer: {}'.format(assertion_instance.issuer.name))
            if assertion_instance.signature:
                raise ValidationError('Cannot sign Assertion for Badgeclass {} with recipient identifier {}. Assertion already signed.'.format(assertion_instance.badgeclass.name, assertion_instance.recipient_identifier))
            assertion_instances.append(assertion_instance)

            timestamp = AssertionTimeStamp.objects.get(badge_instance=assertion_instance)
            js = timestamp.get_json_with_proof()
            batch_of_assertion_json.append(js)
        successful_assertions = []
        user.current_symmetric_key.validate_password(password)
        try:
            private_key = tsob.create_new_private_key(password, user.current_symmetric_key)
        except ValueError as e:
            raise ValidationError(str(e))
        try:
            signed_badges = tsob.sign_badges(batch_of_assertion_json,
                                             private_key,
                                             user.current_symmetric_key,
                                             password)
        except ValueError as e:
            raise ValidationError(str(e))
        for signed_badge in signed_badges:
            signature = signed_badge['signature']
            matching_assertion = [ass for ass in assertion_instances if ass.identifier == signed_badge['plain_badge']['id']]
            if len(matching_assertion) > 1:
                raise ValidationError('Signing failed: Signed json could not be matched to a BadgeInstance')
            matching_assertion = matching_assertion[0]
            matching_assertion.rebake(signature=signature, replace_image=True, save=False)
            matching_assertion.signature = signature
            matching_assertion.public_key_issuer.public_key = private_key.public_key
            matching_assertion.public_key_issuer.save()
            matching_assertion.save()
            AssertionTimeStamp.objects.get(badge_instance=matching_assertion).delete()
            matching_assertion.notify_earner(attach_image=True)
            successful_assertions.append(matching_assertion)
        serializer_class = self.get_serializer_class()
        serializer_instance = serializer_class()
        response = [serializer_instance.to_representation(assertion) for assertion in successful_assertions]
        return Response(status=status.HTTP_201_CREATED, data=response)


class BatchAssertionsIssue(VersionedObjectMixin, BaseEntityView):
    model = BadgeClass  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
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
        def _include_extras(a):
            a['create_notification'] = create_notification
            if request.data.get('expires_at'):  # include expiry too
                a['expires'] = datetime.datetime.strptime(request.data['expires_at'], '%d/%m/%Y')
            return a
        recipients = list(map(_include_extras, request.data.get('recipients')))

        # save serializers
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(many=True, data=recipients, context=context)
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
            return dict(response, reason=str(e))

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
    POST to issue a new assertion, or multiple assertions
    """
    model = BadgeClass  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, MayIssueBadgeClass, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
    create_event = badgrlog.BadgeInstanceCreatedEvent
    valid_scopes = ["rw:issuer", "rw:issuer:*"]
    http_method_names = ['get']

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


class IssuerBadgeInstanceList(UncachedPaginatedViewMixin, VersionedObjectMixin, BaseEntityListView):
    """
    Retrieve all assertions within one issuer
    """
    model = Issuer  # used by get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsStaff, BadgrOAuthTokenHasEntityScope)
    v1_serializer_class = BadgeInstanceSerializerV1
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
        try:
            assertion = self.get_object(request, **kwargs)
        except Http404 as e:
            return Response({'error': 'You do not have permission. Check your assigned role in the Issuer'}, status=HTTP_404_NOT_FOUND)
        if not self.has_object_permissions(request, assertion):
            return Response({'error': 'You do not have permission. Check your assigned role in the Issuer'}, status=HTTP_404_NOT_FOUND)
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
