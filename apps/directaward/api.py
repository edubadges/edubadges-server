import datetime

from django.core.exceptions import BadRequest
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgrsocialauth.permissions import IsSuperUser
from directaward.models import DirectAward, DirectAwardBundle, DirectAwardAuditTrail
from directaward.permissions import IsDirectAwardOwner
from directaward.serializer import DirectAwardBundleSerializer, DirectAwardAuditTrailSerializer
from directaward.signals import audit_trail_signal
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite import settings
from mainsite.exceptions import (
    BadgrValidationError,
    BadgrValidationFieldError,
)
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail


def direct_award_remove_cache(direct_award):
    direct_award.bundle.remove_cached_data(['cached_direct_awards'])
    direct_award.badgeclass.remove_cached_data(['cached_direct_awards'])
    direct_award.badgeclass.remove_cached_data(['cached_direct_award_bundles'])


# Several reusable, generic request and responses
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
    'scheduled_at': serializers.CharField(required=False, allow_null=True),
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

permission_denied_response = OpenApiResponse(
    response=inline_serializer(name='PermissionDeniedResponse', fields={'detail': serializers.CharField()}),
    examples=[
        OpenApiExample(name='Forbidden Response', value={'detail': 'Authentication credentials were not provided.'})
    ],
)

not_found_response = OpenApiResponse(
    response=inline_serializer(
        name='DirectAwardNotFoundResponse',
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
                    'badgeclass': serializers.CharField(),
                    'entity_id': serializers.CharField(),
                },
            ),
            examples=[
                OpenApiExample(
                    'Successful Response',
                    value={
                        'badgeclass': 'etryui25asda',
                        'entity_id': 'bundle-456',
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
        403: permission_denied_response,
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
        request=inline_serializer(name='DirectAwardGetBundleRequest', fields={'entity_id': serializers.CharField()}),
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
            403: permission_denied_response,
            404: not_found_response,
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
            403: permission_denied_response,
            404: not_found_response,
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
                    badgeclass_id=direct_award_db.badgeclass_id,
                    summary=f'Directaward revoked with reason {revocation_reason}',
                )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='REVOKE',
                    direct_award_id=direct_award['entity_id'],
                    badgeclass_id=0,
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
            403: permission_denied_response,
            404: not_found_response,
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
                    badgeclass_id=direct_award_db.badgeclass_id,
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
            403: permission_denied_response,
            404: not_found_response,
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
                    badgeclass_id=direct_award.badgeclass_id,
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
                badgeclass_id=direct_award.badgeclass_id,
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
                badgeclass_id=direct_award.badgeclass_id,
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
            403: permission_denied_response,
            404: not_found_response,
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
        delete_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=settings.DIRECT_AWARDS_DELETION_THRESHOLD_DAYS
        )
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
                        badgeclass_id=direct_award_db.badgeclass_id,
                        summary=f'Awarded eduBadge has been deleted with reason {revocation_reason}',
                    )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method='DELETE',
                    direct_award_id=direct_award['entity_id'],
                    badgeclass_id=0,
                    summary=f'Exception: {e}',
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


class DirectAwardAuditTrailView(APIView):
    permission_classes = (IsSuperUser,)

    @extend_schema(
        description='Get all direct award audit trail entries (superuser only)',
        methods=['GET'],
        responses={
            200: OpenApiResponse(
                response=DirectAwardAuditTrailSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Successful Response',
                        value=[
                            {
                                'action_datetime': '2025-01-15T10:30:00Z',
                                'user': 'john.doe@example.edu',
                                'badgeclass_name': 'Introduction to Python Programming',
                                'institution_name': 'Example University',
                                'recipient_email': 'student19example@gmail.com',
                                'recipient_eppn': 'student19@example',
                            }
                        ],
                    )
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, *args, **kwargs):
        audit_trails = DirectAwardAuditTrail.objects.filter(action='CREATE').order_by('-action_datetime')
        serializer = DirectAwardAuditTrailSerializer(audit_trails, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
