import logging

import requests
from badgeuser.models import StudentAffiliation
from badgrsocialauth.providers.eduid.provider import EduIDProvider
from directaward.models import DirectAward, DirectAwardBundle
from django.conf import settings
from django.db.models import Q, Subquery
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from issuer.models import BadgeInstance, BadgeInstanceCollection
from issuer.serializers import BadgeInstanceCollectionSerializer
from lti_edu.models import StudentsEnrolled
from mainsite.exceptions import BadgrApiException400
from mainsite.mobile_api_authentication import TemporaryUser
from mainsite.permissions import MobileAPIPermission
from mobile_api.helper import NoValidatedNameException, RevalidatedNameException, process_eduid_response
from mobile_api.serializers import (
    BadgeCollectionSerializer,
    BadgeInstanceDetailSerializer,
    BadgeInstanceSerializer,
    DirectAwardDetailSerializer,
    DirectAwardSerializer,
    StudentsEnrolledDetailSerializer,
    StudentsEnrolledSerializer,
    UserSerializer,
)
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

permission_denied_response = OpenApiResponse(
    response=inline_serializer(name='PermissionDeniedResponse', fields={'detail': serializers.CharField()}),
    examples=[
        OpenApiExample(name='Forbidden Response', value={'detail': 'Authentication credentials were not provided.'})
    ],
)


class Login(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Login and validate the user',
        responses={
            403: permission_denied_response,
            200: OpenApiResponse(
                description='Successful responses with examples',
                response=dict,  # or inline custom serializer class
                examples=[
                    OpenApiExample(
                        'User needs to link account in eduID',
                        value={'status': 'link-account'},
                        description="Redirect the user back to eduID with 'acr_values' = 'https://eduid.nl/trust/validate-names'",
                        response_only=True,
                    ),
                    OpenApiExample(
                        'User needs to revalidate name in eduID',
                        value={'status': 'revalidate-name'},
                        description="Redirect the user back to eduID with 'acr_values' = 'https://eduid.nl/trust/validate-names'",
                        response_only=True,
                    ),
                    OpenApiExample(
                        'User needs to agree to terms',
                        value={
                            'email': 'jdoe@example.com',
                            'last_name': 'Doe',
                            'first_name': 'John',
                            'validated_name': 'John Doe',
                            'schac_homes': ['university-example.org'],
                            'terms_agreed': False,
                            'termsagreement_set': [],
                        },
                        description="Show the terms and use the 'accept-general-terms' endpoint",
                        response_only=True,
                    ),
                    OpenApiExample(
                        'User valid',
                        value={
                            'email': 'jdoe@example.com',
                            'last_name': 'Doe',
                            'first_name': 'John',
                            'validated_name': 'John Doe',
                            'schac_homes': ['university-example.org'],
                            'terms_agreed': True,
                            'termsagreement_set': [
                                {
                                    'agreed': True,
                                    'agreed_version': 1,
                                    'terms': {'terms_type': 'service_agreement_student'},
                                },
                                {
                                    'agreed': True,
                                    'agreed_version': 1,
                                    'terms': {'terms_type': 'terms_of_service', 'institution': None},
                                },
                            ],
                        },
                        description='The user is valid, proceed with fetching all badge-instances and OPEN direct-awards',
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request, **kwargs):
        logger = logging.getLogger('Badgr.Debug')

        user = request.user
        """
        Check if the user is known, has agreed to the terms and has a validated_name. If the user is not known
        then check if there is a validate name and provision the user. If all is well, then return the user information
        """
        temporary_user = isinstance(user, TemporaryUser)
        if temporary_user:
            bearer_token = user.bearer_token
        else:
            authorization = request.environ.get('HTTP_AUTHORIZATION')
            bearer_token = authorization[len('bearer ') :]

        headers = {
            'Accept': 'application/json, application/json;charset=UTF-8',
            'Authorization': f'Bearer {bearer_token}',
        }
        url = f'{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links'
        response = requests.get(url, headers=headers, timeout=60)
        if response.status_code != 200:
            error = f'Server error: eduID eppn endpoint error ({response.status_code})'
            logger.error(error)
            return Response(data={'error': str(error)}, status=response.status_code)

        eduid_response = response.json()
        validated_names = [info['validated_name'] for info in eduid_response if 'validated_name' in info]
        if not validated_names:
            # The user must go back to eduID and link an account
            return Response(data={'status': 'link-account'})
        if temporary_user:
            # User must be created / provisioned together with social account
            provider = EduIDProvider(request)
            social_login = provider.sociallogin_from_response(request, user.user_payload)
            social_login.save(request)
            user = social_login.user
        try:
            process_eduid_response(eduid_response, user)
        except RevalidatedNameException:
            return Response(data={'status': 'revalidate-name'})
        except NoValidatedNameException:
            return Response(data={'status': 'link-account'})

        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class AcceptGeneralTerms(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Accept the general terms',
        responses={
            200: OpenApiResponse(
                description='Terms accepted successfully',
                response=inline_serializer(
                    name='AcceptGeneralTermsResponse', fields={'status': serializers.CharField()}
                ),
                examples=[
                    OpenApiExample(
                        'Terms Accepted',
                        value={'status': 'ok'},
                        description='User has successfully accepted the general terms',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, **kwargs):
        logger = logging.getLogger('Badgr.Debug')
        user = request.user
        user.accept_general_terms()
        user.save()
        logger.info(f'Accepted general terms for user {user.email}')
        return Response(data={'status': 'ok'})


class BadgeInstances(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all assertions for the user',
        responses={
            200: OpenApiResponse(
                description='List of badge instances',
                response=BadgeInstanceSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Badge Instances List',
                        value=[
                            {
                                'entity_id': '123e4567-e89b-12d3-a456-426614174000',
                                'badgeclass': {
                                    'entity_id': 'badgeclass-123',
                                    'name': 'Python Programming',
                                    'description': 'Completed Python programming course',
                                    'image': 'https://example.com/badge-image.png',
                                },
                                'issued_on': '2023-01-15T10:30:00Z',
                                'recipient_identifier': 'user@example.com',
                            },
                        ],
                        description='Array of badge instances belonging to the user',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related

        instances = (
            BadgeInstance.objects.select_related('badgeclass')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .filter(user=request.user)
        )
        serializer = BadgeInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class BadgeInstanceDetail(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get details for a badge instance',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the badge instance',
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Badge instance details',
                response=BadgeInstanceDetailSerializer,
                examples=[
                    OpenApiExample(
                        'Badge Instance Details',
                        value={
                            'entity_id': '123e4567-e89b-12d3-a456-426614174000',
                            'badgeclass': {
                                'entity_id': 'badgeclass-123',
                                'name': 'Python Programming',
                                'description': 'Completed Python programming course',
                                'image': 'https://example.com/badge-image.png',
                                'criteria': 'https://example.com/criteria',
                            },
                            'issued_on': '2023-01-15T10:30:00Z',
                            'recipient_identifier': 'user@example.com',
                            'evidence': 'https://example.com/evidence',
                            'narrative': 'User completed all assignments and final project',
                        },
                        description='Detailed information about a specific badge instance',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Badge instance not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Badge instance not found'},
                        description='The requested badge instance does not exist or user does not have access',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, entity_id, **kwargs):
        instance = (
            BadgeInstance.objects.select_related('badgeclass')
            .prefetch_related('badgeclass__badgeclassextension_set')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .filter(user=request.user)
            .filter(entity_id=entity_id)
            .get()
        )
        serializer = BadgeInstanceDetailSerializer(instance)
        return Response(serializer.data)


class UnclaimedDirectAwards(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all unclaimed awarded badges for the user',
        responses={
            200: OpenApiResponse(
                description='List of unclaimed direct awards',
                response=DirectAwardSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Unclaimed Direct Awards',
                        value=[
                            {
                                'entity_id': 'direct-award-123',
                                'badgeclass': {
                                    'entity_id': 'badgeclass-456',
                                    'name': 'Data Science Certificate',
                                    'description': 'Awarded for completing data science program',
                                    'image': 'https://example.com/data-science-badge.png',
                                },
                                'status': 'Unaccepted',
                                'created_at': '2023-02-20T09:15:00Z',
                                'recipient_email': 'user@example.com',
                            },
                        ],
                        description='Array of unclaimed direct awards available to the user',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related
        affiliations = StudentAffiliation.objects.filter(user=request.user)

        direct_awards = (
            DirectAward.objects.select_related('badgeclass')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .filter(
                Q(eppn__in=Subquery(affiliations.values('eppn')))
                | Q(recipient_email=request.user.email, bundle__identifier_type=DirectAwardBundle.IDENTIFIER_EMAIL)
            )
            .filter(status='Unaccepted')
        )

        serializer = DirectAwardSerializer(direct_awards, many=True)
        return Response(serializer.data)


class DirectAwardDetail(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get direct award details for the user',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the direct award',
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Direct award details',
                response=DirectAwardDetailSerializer,
                examples=[
                    OpenApiExample(
                        'Direct Award Details',
                        value=[
                            {
                                'id': 9596,
                                'created_at': '2026-01-16T10:56:44.293475+01:00',
                                'entity_id': 'y8uStIzMQ--JY59DIKnvWw',
                                'badgeclass': {
                                    'id': 6,
                                    'name': 'test direct award',
                                    'entity_id': 'B3uWEIZSTh6wniHBbzVtbA',
                                    'image_url': 'https://api-demo.edubadges.nl/media/uploads/badges/issuer_badgeclass_6c3b5f04-292b-41fa-8df6-d5029386bd3f.png',
                                    'issuer': {
                                        'name_dutch': 'SURF Edubadges',
                                        'name_english': 'SURF Edubadges',
                                        'image_dutch': 'null',
                                        'image_english': '/media/uploads/issuers/issuer_logo_ccd075bb-23cb-40b2-8780-b5a7eda9de1c.png',
                                        'faculty': {
                                            'name_dutch': 'SURF',
                                            'name_english': 'SURF',
                                            'image_dutch': 'null',
                                            'image_english': 'null',
                                            'on_behalf_of': 'false',
                                            'on_behalf_of_display_name': 'null',
                                            'on_behalf_of_url': 'null',
                                            'institution': {
                                                'name_dutch': 'University Voorbeeld',
                                                'name_english': 'University Example',
                                                'image_dutch': '/media/uploads/institution/d0273589-2c7a-4834-8c35-fef4695f176a.png',
                                                'image_english': '/media/uploads/institution/eae5465f-98b1-4849-ac2d-47d4e1cd1252.png',
                                                'identifier': 'university-example.org',
                                                'alternative_identifier': 'university-example.org.tempguestidp.edubadges.nl',
                                                'grondslag_formeel': 'gerechtvaardigd_belang',
                                                'grondslag_informeel': 'gerechtvaardigd_belang',
                                            },
                                        },
                                    },
                                },
                            }
                        ],
                        description='Detailed information about a specific direct award',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Direct award not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Direct award not found'},
                        description='The requested direct award does not exist or user does not have access',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    # ForeignKey / OneToOneField → select_related
    # ManyToManyField / reverse FK → prefetch_related
    def get(self, request, entity_id, **kwargs):
        instance = (
            DirectAward.objects.select_related('badgeclass')
            .prefetch_related('badgeclass__badgeclassextension_set')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .prefetch_related('badgeclass__issuer__faculty__institution__terms')
            .filter(entity_id=entity_id)
            .get()
        )
        serializer = DirectAwardDetailSerializer(instance)
        return Response(serializer.data)


class Enrollments(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all enrollments for the user',
        responses={
            200: OpenApiResponse(
                description='List of enrollments',
                response=StudentsEnrolledSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Enrollments List',
                        value=[
                            {
                                'entity_id': 'enrollment-123',
                                'badge_class': {
                                    'entity_id': 'badgeclass-789',
                                    'name': 'Advanced Machine Learning',
                                    'description': 'Enrolled in advanced ML course',
                                },
                                'user': 'user@example.com',
                                'date_enrolled': '2023-03-10T14:25:00Z',
                                'date_awarded': None,
                                'status': 'Active',
                            },
                        ],
                        description='Array of course enrollments for the user',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related
        enrollments = (
            StudentsEnrolled.objects.select_related('badge_class')
            .select_related('badge_class__issuer')
            .select_related('badge_class__issuer__faculty')
            .select_related('badge_class__issuer__faculty__institution')
            .filter(user=request.user)
        )

        serializer = StudentsEnrolledSerializer(enrollments, many=True)
        return Response(serializer.data)


class EnrollmentDetail(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get enrollment details for the user',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the enrollment',
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Enrollment details',
                response=StudentsEnrolledDetailSerializer,
                examples=[
                    OpenApiExample(
                        'Enrollment Details',
                        value={
                            'entity_id': 'enrollment-123',
                            'badge_class': {
                                'entity_id': 'badgeclass-789',
                                'name': 'Advanced Machine Learning',
                                'description': 'Enrolled in advanced ML course',
                                'image': 'https://example.com/ml-badge.png',
                                'criteria': 'https://example.com/criteria',
                            },
                            'user': 'user@example.com',
                            'date_enrolled': '2023-03-10T14:25:00Z',
                            'date_awarded': None,
                            'status': 'Active',
                            'issuer': {
                                'name': 'University of Example',
                                'url': 'https://example.edu',
                            },
                        },
                        description='Detailed information about a specific enrollment',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Enrollment not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Enrollment not found'},
                        description='The requested enrollment does not exist or user does not have access',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    # ForeignKey / OneToOneField → select_related
    # ManyToManyField / reverse FK → prefetch_related
    def get(self, request, entity_id, **kwargs):
        enrollment = (
            StudentsEnrolled.objects.select_related('badgeclass')
            .prefetch_related('badgeclass__badgeclassextension_set')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .filter(user=request.user)
            .filter(entity_id=entity_id)
            .get()
        )
        serializer = StudentsEnrolledDetailSerializer(enrollment)
        return Response(serializer.data)

    @extend_schema(
        methods=['DELETE'],
        description='Delete enrollment for the user',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the enrollment',
            )
        ],
        responses={
            204: OpenApiResponse(
                description='Enrollment deleted successfully',
                examples=[
                    OpenApiExample(
                        'Deleted',
                        value=None,
                        description='Enrollment was successfully deleted',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Enrollment not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Enrollment not found'},
                        description='The requested enrollment does not exist',
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(
                description='Cannot delete awarded enrollment',
                examples=[
                    OpenApiExample(
                        'Awarded Enrollment',
                        value={'detail': 'Awarded enrollments cannot be withdrawn'},
                        description='Cannot delete an enrollment that has already been awarded',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def delete(self, request, entity_id, **kwargs):
        enrollment = get_object_or_404(StudentsEnrolled, user=request.user, entity_id=entity_id)
        if enrollment.date_awarded:
            raise BadgrApiException400('Awarded enrollments cannot be withdrawn', 206)
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgeCollectionsListView(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all badge collections for the user',
        responses={
            200: OpenApiResponse(
                description='List of badge collections',
                response=BadgeCollectionSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Badge Collections List',
                        value=[
                            {
                                'entity_id': 'YpQpVLu6QsmXiWZ7YhrSPQ',
                                'name': 'My Achievements',
                                'desacription': 'Collection of my programming achievements',
                                'badge_instances': [311, 312],
                            },
                        ],
                        description='Array of badge collections created by the user',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, **kwargs):
        collections = BadgeInstanceCollection.objects.filter(user=request.user)
        serializer = BadgeCollectionSerializer(collections, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=BadgeInstanceCollectionSerializer,
        description='Create a new BadgeInstanceCollection',
        responses={
            201: OpenApiResponse(
                description='Badge collection created successfully',
                response=BadgeInstanceCollectionSerializer,
                examples=[
                    OpenApiExample(
                        'Created Collection',
                        value={
                            'entity_id': 'collection-123',
                            'name': 'My Achievements',
                            'description': 'Collection of my programming achievements',
                            'badge_instances': [311],
                        },
                        description='Newly created badge collection',
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(
                description='Invalid request data',
                examples=[
                    OpenApiExample(
                        'Invalid Data',
                        value={'name': ['This field is required.']},
                        description='Validation errors in the request data',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def post(self, request):
        serializer = BadgeInstanceCollectionSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        badge_collection = serializer.save()
        return Response(BadgeInstanceCollectionSerializer(badge_collection).data, status=status.HTTP_201_CREATED)


class BadgeCollectionsDetailView(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        request=BadgeInstanceCollectionSerializer,
        description='Update an existing BadgeInstanceCollection by ID',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the collection',
            )
        ],
        responses={
            200: OpenApiResponse(
                description='Badge collection updated successfully',
                response=BadgeInstanceCollectionSerializer,
                examples=[
                    OpenApiExample(
                        'Updated Collection',
                        value={
                            'entity_id': 'collection-123',
                            'name': 'My Updated Achievements',
                            'description': 'Updated collection of my programming achievements',
                            'badge_instances': [
                                {
                                    'entity_id': 'badge-456',
                                    'name': 'Python Programming',
                                },
                            ],
                        },
                        description='Updated badge collection',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Badge collection not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Badge collection not found'},
                        description='The requested badge collection does not exist',
                        response_only=True,
                    ),
                ],
            ),
            400: OpenApiResponse(
                description='Invalid request data',
                examples=[
                    OpenApiExample(
                        'Invalid Data',
                        value={'name': ['This field is required.']},
                        description='Validation errors in the request data',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def put(self, request, entity_id):
        badge_collection = get_object_or_404(BadgeInstanceCollection, user=request.user, entity_id=entity_id)
        serializer = BadgeInstanceCollectionSerializer(
            badge_collection, data=request.data, context={'request': request}, partial=False
        )
        serializer.is_valid(raise_exception=True)
        badge_collection = serializer.save()
        return Response(BadgeInstanceCollectionSerializer(badge_collection).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=None,
        description='Delete a BadgeInstanceCollection by ID',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the enrollment',
            )
        ],
        responses={
            204: OpenApiResponse(
                description='Badge collection deleted successfully',
                examples=[
                    OpenApiExample(
                        'Deleted',
                        value=None,
                        description='Badge collection was successfully deleted',
                        response_only=True,
                    ),
                ],
            ),
            404: OpenApiResponse(
                description='Badge collection not found',
                examples=[
                    OpenApiExample(
                        'Not Found',
                        value={'detail': 'Badge collection not found'},
                        description='The requested badge collection does not exist',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def delete(self, request, entity_id):
        badge_collection = get_object_or_404(BadgeInstanceCollection, entity_id=entity_id, user=request.user)
        badge_collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
