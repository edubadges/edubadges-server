import datetime
import threading

from django.core.exceptions import BadRequest
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from directaward.models import DirectAward, DirectAwardBundle
from directaward.permissions import IsDirectAwardOwner
from directaward.serializer import DirectAwardSerializer, DirectAwardBundleSerializer
from directaward.signals import audit_trail_signal
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite import settings
from mainsite.exceptions import (
    BadgrValidationError,
    BadgrValidationFieldError,
)
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail
from staff.permissions import HasObjectPermission


def direct_award_remove_cache(direct_award):
    direct_award.bundle.remove_cached_data(['cached_direct_awards'])
    direct_award.badgeclass.remove_cached_data(['cached_direct_awards'])
    direct_award.badgeclass.remove_cached_data(['cached_direct_award_bundles'])


direct_awards_response = serializers.ListField(
    child=inline_serializer(
        name='DirectAwardsResponse',
        fields={
            'eppn': serializers.CharField(),
            'recipient_email': serializers.CharField(),
            'status': serializers.CharField(),
        },
        allow_null=False,
    )
)

direct_awards_request = {
    'badgeclass': serializers.CharField(),
    'direct_awards': serializers.ListField(
        child=inline_serializer(
            name='DirectAwardDetailsSerializer',
            fields={
                'eppn': serializers.CharField(),
                'recipient_email': serializers.EmailField(),
            },
        )
    ),
    'sis_user_id': serializers.CharField(),
    'batch_mode': serializers.BooleanField(),
    'lti_import': serializers.BooleanField(),
    'status': serializers.CharField(),
    'identifier_type': serializers.CharField(),
    'scheduled_at': serializers.CharField(),
    'notify_recipients': serializers.BooleanField(),
}

unsuccessful_response = serializers.ListField(
    child=inline_serializer(
        name='DirectAwardsUnclaimedResponse',
        fields={
            'error': serializers.CharField(),
            'eppn': serializers.CharField(),
            'recipient_email': serializers.CharField(),
        },
    )
)


@extend_schema(
    description='Create a direct award bundle',
    methods=['POST'],
    request=inline_serializer(name='DirectAwardCreateBundleRequest', fields=direct_awards_request),
    responses={
        201: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardCreateBundleResponse',
                fields={
                    'entity_id': serializers.CharField(),
                    'status': serializers.CharField(),
                    'created_at': serializers.CharField(),
                    'direct_awards': direct_awards_response,
                    'un_successful_direct_awards': unsuccessful_response,
                },
            ),
            examples=[
                OpenApiExample(
                    'Successful Response',
                    value={
                        'entity_id': 'bundle-456',
                        'status': 'Scheduled',
                        'created_at': '2025-01-01T12:00:00Z',
                        'direct_awards': [
                            {'eppn': 'user@example.edu', 'recipient_email': 'user@example.edu', 'status': 'Scheduled'}
                        ],
                        'un_successful_direct_awards': [
                            {
                                'error': 'DirectAward already exists',
                                'eppn': 'user2@example.edu',
                                'recipient_email': 'user2@example.edu',
                            }
                        ],
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardCreateBundleBadRequestRepsonse', fields={'error': serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    'Return 400 error bad request',
                    value={'error': 'Bad request'},
                    response_only=True,
                ),
            ],
        ),
        403: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardCreateBundlePermissionDeniedResponse', fields={'error': serializers.CharField()}
            ),
            examples=[
                OpenApiExample(
                    'Return 403 permission denied',
                    value={'error': 'Permission denied'},
                    response_only=True,
                ),
            ],
        ),
    },
    examples=[
        OpenApiExample(
            'Create Direct Award Bundle',
            value={
                'badgeclass': 'badgeclass-123',
                'direct_awards': [{'eppn': 'user@example.edu', 'recipient_email': 'user@example.edu'}],
                'sis_user_id': 'sis-123',
                'batch_mode': True,
                'lti_import': False,
                'status': 'Active',
                'identifier_type': 'eppn',
                'scheduled_at': '2025-01-01T12:00:00Z',
                'notify_recipients': True,
            },
            request_only=True,
        )
    ],
)
class DirectAwardBundleList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = DirectAwardBundleSerializer
    permission_map = {'POST': 'may_award'}
    http_method_names = ['post']


class DirectAwardBundleView(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    permission_map = {'POST': 'may_award'}

    @extend_schema(
        description='Get direct award bundle information',
        methods=['GET'],
        request={'application/json': {'entity_id': 'string'}},
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardGetBundleResponse',
                    fields={
                        'initial_total': serializers.IntegerField(),
                        'status': serializers.CharField(),
                        'badgeclass': serializers.CharField(),
                        'assertion_count': serializers.IntegerField(),
                        'direct_award_count': serializers.IntegerField(),
                        'direct_award_rejected_count': serializers.IntegerField(),
                        'direct_award_scheduled_count': serializers.IntegerField(),
                        'direct_award_deleted_count': serializers.IntegerField(),
                        'direct_award_revoked_count': serializers.IntegerField(),
                        'direct_awards': serializers.ListField(
                            child=inline_serializer(
                                name='DirectAward',
                                fields={
                                    'recipient_email': serializers.CharField(),
                                    'eppn': serializers.CharField(),
                                    'status': serializers.CharField(),
                                    'entity_id': serializers.CharField(),
                                },
                            )
                        ),
                        'badge_assertions': serializers.ListField(
                            child=inline_serializer(
                                name='BadgeAssertion',
                                fields={
                                    'full_name': serializers.CharField(),
                                    'email': serializers.CharField(),
                                    'public': serializers.BooleanField(),
                                    'revoked': serializers.BooleanField(),
                                    'entity_id': serializers.CharField(),
                                    'eppn': serializers.CharField(),
                                },
                            )
                        ),
                    },
                ),
                examples=[
                    OpenApiExample(
                        'Successful Response',
                        value={
                            'initial_total': 10,
                            'status': 'Active',
                            'badgeclass': 'Leadership Award',
                            'assertion_count': 8,
                            'direct_award_count': 10,
                            'direct_award_rejected_count': 1,
                            'direct_award_scheduled_count': 1,
                            'direct_award_deleted_count': 0,
                            'direct_award_revoked_count': 0,
                            'direct_awards': [
                                {
                                    'recipient_email': 'user@example.edu',
                                    'eppn': 'user123',
                                    'status': 'Accepted',
                                    'entity_id': 'da-001',
                                }
                            ],
                            'badge_assertions': [
                                {
                                    'full_name': 'John Doe',
                                    'email': 'john.doe@example.edu',
                                    'public': True,
                                    'revoked': False,
                                    'entity_id': 'ba-123',
                                    'eppn': 'john123',
                                }
                            ],
                        },
                    )
                ],
            ),
            403: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardGetBundlePermissionDeniedResponse', fields={'detail': serializers.CharField()}
                ),
                examples=[
                    OpenApiExample(
                        name='Forbidden Response', value={'detail': 'Authentication credentials were not provided.'}
                    )
                ],
            ),
            404: OpenApiResponse(
                description='Error: Not Found',
            ),
        },
        examples=[
            OpenApiExample('Get Bundle Request Example', value={'entity_id': 'bundle-123'}, request_only=True),
        ],
    )
    def get(self, request, **kwargs):
        try:
            award_bundle = DirectAwardBundle.objects.get(entity_id=kwargs.get('entity_id'))
        except DirectAwardBundle.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        def convert_direct_award(direct_award):
            return {
                'recipient_email': direct_award.recipient_email,
                'eppn': direct_award.eppn,
                'status': direct_award.status,
                'entity_id': direct_award.entity_id,
            }

        def convert_badge_assertion(badge_instance):
            user = badge_instance.user
            return {
                'full_name': user.full_name,
                'email': user.email,
                'public': badge_instance.public,
                'revoked': badge_instance.revoked,
                'entity_id': badge_instance.entity_id,
                'eppn': user.eppns[0] if user.eppns else [],
            }

        results = {
            'initial_total': award_bundle.initial_total,
            'status': award_bundle.status,
            'badgeclass': award_bundle.badgeclass.name,
            'assertion_count': award_bundle.assertion_count,
            'direct_award_count': award_bundle.direct_award_count,
            'direct_award_rejected_count': award_bundle.direct_award_rejected_count,
            'direct_award_scheduled_count': award_bundle.direct_award_scheduled_count,
            'direct_award_deleted_count': award_bundle.direct_award_deleted_count,
            'direct_award_revoked_count': award_bundle.direct_award_revoked_count,
            'direct_awards': [convert_direct_award(da) for da in award_bundle.directaward_set.all()],
            'badge_assertions': [convert_badge_assertion(ba) for ba in award_bundle.badgeinstance_set.all()],
        }

        return Response(results, status=status.HTTP_200_OK)


class DirectAwardRevoke(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    @extend_schema(
        description='Revoke direct awards',
        methods=['POST'],
        request=inline_serializer(
            name='DirectAwardRevokeRequest',
            fields={
                'revocation_reason': serializers.CharField(),
                'direct_awards': serializers.ListField(
                    child=inline_serializer(
                        name='NestedInlineOneOffSerializer',
                        fields={
                            'entity_id': serializers.CharField(),
                        },
                        allow_null=False,
                    )
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardRevokeResponse',
                    fields={'result': serializers.CharField(), 'un_successful_direct_awards': unsuccessful_response},
                ),
                examples=[
                    OpenApiExample(
                        'DirectAward Revoke Partial Response',
                        value={
                            'result': 'ok',
                            'un_successful_direct_awards': [
                                {
                                    'error': 'DirectAward already exists',
                                    'eppn': 'user2@example.edu',
                                    'recipient_email': 'user2@example.edu',
                                }
                            ],
                        },
                    ),
                    OpenApiExample(
                        'DirectAward Revoke Successful Response',
                        value={'result': 'ok', 'un_successful_direct_awards': []},
                    ),
                ],
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardNoValidRevokedResponse', fields={'error': serializers.CharField()}
                ),
                examples=[
                    OpenApiExample(
                        'DirectAward Revoke No Valid Response',
                        value={'error': 'No valid DirectAwards are revoked. All of them were rejected:'},
                    )
                ],
            ),
            404: {'error': 'Direct Award Bundle not found'},
        },
        examples=[
            OpenApiExample(
                'Direct Award Revoke Request Example',
                value={
                    'revocation_reason': 'Violation of terms',
                    'direct_awards': [{'entity_id': 'da-001'}],
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, **kwargs):
        """
        Revoke direct awards
        """
        revocation_reason = request.data.get('revocation_reason', None)
        direct_awards = request.data.get('direct_awards', None)
        if not revocation_reason:
            raise BadgrValidationFieldError('revocation_reason', 'This field is required', 999)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', 'This field is required', 999)
        un_successful_direct_awards = []
        successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award['entity_id'])
                if not direct_award_db.get_permissions(request.user)['may_award']:
                    raise BadgrValidationError('No permissions', 100)
                direct_award_db.revoke(revocation_reason)
                successful_direct_awards.append(direct_award_db)
                direct_award_remove_cache(direct_award_db)
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='REVOKE',
                    direct_award_id=direct_award_db.entity_id,
                    summary=f'Directaward revoked with reason {revocation_reason}',
                )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='REVOKE',
                    direct_award_id=direct_award['entity_id'],
                    summary=f'Direct award not revoked, error: {str(e)}',
                )
                un_successful_direct_awards.append(
                    {'error': str(e), 'eppn': direct_award.get('eppn'), 'email': direct_award.get('recipient_email')}
                )
        if not successful_direct_awards:
            raise BadRequest(
                f'No valid DirectAwards are revoked. All of them were rejected: {str(un_successful_direct_awards)}'
            )
        return Response(
            {'result': 'ok', 'un_successful_direct_awards': un_successful_direct_awards}, status=status.HTTP_200_OK
        )


class DirectAwardResend(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    @extend_schema(
        description='Resend direct awards',
        methods=['POST'],
        request=inline_serializer(
            name='DirectAwardResendRequest',
            fields={
                'direct_awards': serializers.ListField(
                    child=inline_serializer(
                        name='NestedInlineOneOffSerializer',
                        fields={
                            'entity_id': serializers.CharField(),
                        },
                        allow_null=False,
                    )
                )
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardResendResponse',
                    fields={'result': serializers.CharField(), 'un_successful_direct_awards': unsuccessful_response},
                ),
                examples=[
                    OpenApiExample(
                        'DirectAward Resend Partial Response',
                        value={
                            'result': 'ok',
                            'un_successful_direct_awards': [
                                {
                                    'error': 'DirectAward already exists',
                                    'eppn': 'user2@example.edu',
                                    'recipient_email': 'user2@example.edu',
                                }
                            ],
                        },
                    ),
                    OpenApiExample(
                        'DirectAward Resend Successful Response',
                        value={'result': 'ok', 'un_successful_direct_awards': []},
                    ),
                ],
            ),
            400: OpenApiResponse(
                response=inline_serializer(name='DirectAwardNoValidResend', fields={'error': serializers.CharField()}),
                examples=[
                    OpenApiExample(
                        'DirectAward Resend No Valid Response',
                        value={'error': 'No valid DirectAwards are revoked. All of them were rejected:'},
                    )
                ],
            ),
            404: {'error': 'Direct Award Bundle not found'},
        },
        examples=[
            OpenApiExample(
                'Resend Request Example',
                value={
                    'revocation_reason': 'Violation of terms',
                    'direct_awards': [{'entity_id': 'da-001'}],
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, **kwargs):
        direct_awards = request.data.get('direct_awards', None)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', 'This field is required', 999)
        successful_direct_awards = []
        un_successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award['entity_id'])
                if not direct_award_db.get_permissions(request.user)['may_award']:
                    raise BadgrValidationError('No permissions', 100)
                direct_award_db.resend_at = datetime.datetime.now()
                direct_award_db.save()
                direct_award_remove_cache(direct_award_db)
                successful_direct_awards.append(direct_award_db)
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='RESEND',
                    direct_award_id=direct_award_db.entity_id,
                    summary='Directaward resent',
                )
            except Exception as e:
                un_successful_direct_awards.append(
                    {'error': str(e), 'eppn': direct_award.get('eppn'), 'email': direct_award.get('recipient_email')}
                )

        if not successful_direct_awards:
            raise BadRequest(
                f'No valid DirectAwards are resend. All of them were rejected: {str(un_successful_direct_awards)}'
            )

        def resend_mails(awards):
            for da in awards:
                da.notify_recipient()

        thread = threading.Thread(target=resend_mails, args=(successful_direct_awards,))
        thread.start()

        return Response(
            {'result': 'ok', 'un_successful_direct_awards': un_successful_direct_awards}, status=status.HTTP_200_OK
        )


@extend_schema(
    methods=['PUT'],
    description='Updated a direct award',
    request=inline_serializer(name='DirectAwardUpdateBundleRequest', fields=direct_awards_request),
    responses={
        200: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardUpdateSuccessResponse',
                fields={'result': serializers.CharField(), 'un_successful_direct_awards': unsuccessful_response},
            ),
            examples=[
                OpenApiExample(
                    'Successful Response',
                    value={'result': 'ok', 'un_successful_direct_awards': []},
                ),
                OpenApiExample(
                    'Resend Successful Response',
                    value={'result': 'ok', 'un_successful_direct_awards': []},
                ),
                OpenApiExample(
                    'Resend Partial Failure Response',
                    value={
                        'result': 'ok',
                        'un_successful_direct_awards': [
                            {'error': 'Direct award not found', 'eppn': 'user456', 'email': 'user456@example.edu'}
                        ],
                    },
                ),
            ],
        ),
        400: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardUpdateBadRequestResponse',
                fields={
                    'error': serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    'Invalid Request',
                    value={'error': 'No valid DirectAwards are revoked. All of them were rejected.'},
                ),
            ],
        ),
        404: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardUpdateNotFoundResponse',
                fields={
                    'error': serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    'Not Found',
                    value={'error': 'Direct Award Bundle not found'},
                ),
            ],
        ),
        422: OpenApiResponse(
            response=inline_serializer(
                name='DirectAwardUpdateValidationErrorResponse',
                fields={
                    'revocation_reason': serializers.CharField(),
                    'direct_awards': serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    'Validation Error Response',
                    value={
                        'revocation_reason': 'This field is required',
                        'direct_awards': 'This field is required',
                    },
                    response_only=True,
                ),
            ],
        ),
    },
    examples=[
        OpenApiExample(
            'DirectAward Update Request Example',
            value={
                'badgeclass': 'badge-001',
                'eppn': 'user123',
                'recipient_email': 'user@example.edu',
                'status': 'Active',
                'evidence_url': 'https://example.com/evidence',
                'narrative': 'Achieved top score',
                'name': 'Award Name',
                'description': 'Award Description',
                'grade_achieved': 'A+',
            },
            request_only=True,
        ),
    ],
)
class DirectAwardDetail(BaseEntityDetailView):
    model = DirectAward
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = DirectAwardSerializer
    http_method_names = ['put']
    permission_map = {'PUT': 'may_award'}


class DirectAwardAccept(BaseEntityDetailView):
    model = DirectAward  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsDirectAwardOwner)
    http_method_names = ['post']

    @extend_schema(
        methods=['POST'],
        description='Either accept or reject a direct award (claim)',
        parameters=[
            OpenApiParameter(
                name='accept', required=True, description='Either accept (true) or reject (false)', type=bool
            ),
        ],
        request=inline_serializer(
            name='DirectAwardAcceptRequest',
            fields={'entity_id': serializers.CharField(), 'accept': serializers.BooleanField()},
        ),
        responses={
            200: inline_serializer(
                name='DirectAwardAcceptRejectedResponse',
                fields={
                    'rejected': serializers.BooleanField(),
                },
            ),
            201: inline_serializer(
                name='DirectAwardAcceptAcceptedResponse',
                fields={
                    'entity_id': serializers.CharField(),
                },
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardAcceptBadRequestResponse',
                    fields={
                        'error': serializers.CharField(),
                    },
                ),
                examples=[
                    OpenApiExample(
                        'Invalid Request',
                        value={'error': 'Neither accepted or rejected the direct award'},
                    )
                ],
            ),
            404: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardAcceptNotFoundResponse',
                    fields={
                        'detail': serializers.CharField(),
                    },
                ),
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Not found.'},
                    )
                ],
            ),
            422: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardUnprocessableEntityResponse',
                    fields={
                        'error': serializers.CharField(),
                    },
                ),
                examples=[
                    OpenApiExample(
                        'Unprocessable Entity',
                        value={'error': 'Cannot accept direct award, must accept badgeclass terms first'},
                    )
                ],
            ),
        },
        examples=[
            OpenApiExample(
                'DirectAward Accept Request Example',
                value={
                    'entity_id': 'badge-001',
                    'accept': True,
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request, **kwargs):
        direct_award = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, direct_award):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get('accept', False):  # has accepted it
            if not direct_award.badgeclass.terms_accepted(request.user):
                raise BadgrValidationError(
                    'Cannot accept direct award, must accept badgeclass terms first',
                    999,
                )
            try:
                assertion = direct_award.award(recipient=request.user)
            except BadgrValidationError as err:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='ACCEPT',
                    direct_award_id=direct_award.entity_id,
                    summary='Cannot award as eppn does not match or not member of institution',
                )
                raise err
            direct_award_remove_cache(direct_award)
            direct_award.delete()
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method='ACCEPT',
                direct_award_id=direct_award.entity_id,
                summary='Accepted directaward',
            )
            return Response({'entity_id': assertion.entity_id}, status=status.HTTP_201_CREATED)
        elif not request.data.get('accept', True):  # has rejected it
            direct_award.status = DirectAward.STATUS_REJECTED  # reject it
            direct_award.save()
            direct_award_remove_cache(direct_award)
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method='ACCEPT',
                direct_award_id=direct_award.entity_id,
                summary='Rejected directaward',
            )
            return Response({'rejected': True}, status=status.HTTP_200_OK)
        raise BadgrValidationError('Neither accepted or rejected the direct award', 999)


class DirectAwardDelete(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['put']
    permission_map = {'PUT': 'may_award'}

    @extend_schema(
        methods=['PUT'],
        request=inline_serializer(
            name='DirectAwardDeleteRequest',
            fields={
                'revocation_reason': serializers.CharField(),
                'direct_awards': serializers.ListField(
                    child=inline_serializer(
                        name='NestedInlineOneOffSerializer',
                        fields={
                            'entity_id': serializers.CharField(),
                        },
                        allow_null=False,
                    )
                ),
            },
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardDeleteResponse',
                    fields={'result': serializers.CharField(), 'un_successful_direct_awards': unsuccessful_response},
                ),
                examples=[
                    OpenApiExample(
                        'DirectAward Revoke Partial Response',
                        value={
                            'result': 'ok',
                            'un_successful_direct_awards': [
                                {
                                    'error': 'DirectAward already exists',
                                    'eppn': 'user2@example.edu',
                                    'recipient_email': 'user2@example.edu',
                                }
                            ],
                        },
                    ),
                    OpenApiExample(
                        'DirectAward Revoke Successful Response',
                        value={'result': 'ok', 'un_successful_direct_awards': []},
                    ),
                ],
            ),
            400: OpenApiResponse(
                response=inline_serializer(
                    name='DirectAwardNoValidDeleteResponse', fields={'error': serializers.CharField()}
                ),
                examples=[
                    OpenApiExample(
                        'DirectAward Revoke No Valid Response',
                        value={'error': 'No valid DirectAwards are revoked. All of them were rejected:'},
                    )
                ],
            ),
            404: {'error': 'Direct Award Bundle not found'},
        },
        examples=[
            OpenApiExample(
                'Direct Award Delete Request Example',
                value={
                    'revocation_reason': 'Violation of terms',
                    'direct_awards': [{'entity_id': 'da-001'}],
                },
                request_only=True,
            ),
        ],
    )
    def put(self, request, **kwargs):
        direct_awards = request.data.get('direct_awards', None)
        revocation_reason = request.data.get('revocation_reason', None)
        if not direct_awards:
            raise BadgrValidationFieldError('direct_awards', 'This field is required', 999)
        delete_at = datetime.datetime.utcnow() + datetime.timedelta(days=settings.DIRECT_AWARDS_DELETION_THRESHOLD_DAYS)
        un_successful_direct_awards = []
        successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award['entity_id'])
                if not direct_award_db.get_permissions(request.user)['may_award']:
                    raise BadgrValidationError('No permissions', 100)
                if direct_award_db.status == DirectAward.STATUS_DELETED:
                    un_successful_direct_awards.append(
                        {
                            'error': 'DirectAward has already been deleted',
                            'eppn': direct_award_db.eppn,
                            'email': direct_award_db.recipient_email,
                        }
                    )
                else:
                    direct_award_db.delete_at = delete_at
                    direct_award_db.status = DirectAward.STATUS_DELETED
                    direct_award_db.revocation_reason = revocation_reason
                    direct_award_db.save()
                    successful_direct_awards.append(direct_award_db)
                    direct_award_remove_cache(direct_award_db)
                    html_message = EmailMessageMaker.create_direct_award_deleted_email(direct_award_db)
                    send_mail(
                        subject='Awarded eduBadge has been deleted',
                        message=None,
                        html_message=html_message,
                        recipient_list=[direct_award_db.recipient_email],
                    )
                    audit_trail_signal.send(
                        sender=request.user.__class__,
                        request=request,
                        user=request.user,
                        method='DELETE',
                        direct_award_id=direct_award_db.entity_id,
                        summary=f'Awarded eduBadge has been deleted with reason {revocation_reason}',
                    )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='DELETE',
                    direct_award_id=direct_award['entity_id'],
                    summary=f'{e}',
                )
                un_successful_direct_awards.append(
                    {'error': str(e), 'eppn': direct_award.get('eppn'), 'email': direct_award.get('recipient_email')}
                )
        if not successful_direct_awards:
            raise BadRequest(
                f'No valid DirectAwards are deleted. All of them were rejected: {str(un_successful_direct_awards)}'
            )
        return Response(
            {'result': 'ok', 'un_successful_direct_awards': un_successful_direct_awards}, status=status.HTTP_200_OK
        )
