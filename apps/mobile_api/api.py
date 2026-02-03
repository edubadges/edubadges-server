import logging

import requests
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import ListAPIView

from badgeuser.models import StudentAffiliation
from badgrsocialauth.providers.eduid.provider import EduIDProvider
from directaward.models import DirectAward, DirectAwardBundle
from django.conf import settings
from django.db.models import Q, Subquery, Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)

from institution.models import Institution
from issuer.models import BadgeInstance, BadgeInstanceCollection, BadgeClass
from issuer.serializers import BadgeInstanceCollectionSerializer
from lti_edu.models import StudentsEnrolled
from mainsite.exceptions import BadgrApiException400
from mainsite.mobile_api_authentication import TemporaryUser
from mainsite.permissions import MobileAPIPermission
from mobile_api.filters import CatalogBadgeClassFilter
from mobile_api.helper import NoValidatedNameException, RevalidatedNameException, process_eduid_response
from mobile_api.pagination import CatalogPagination
from mobile_api.serializers import (
    BadgeCollectionSerializer,
    BadgeInstanceDetailSerializer,
    BadgeInstanceSerializer,
    DirectAwardDetailSerializer,
    DirectAwardSerializer,
    StudentsEnrolledDetailSerializer,
    StudentsEnrolledSerializer,
    UserSerializer,
    CatalogBadgeClassSerializer,
    UserProfileSerializer,
    BadgeClassDetailSerializer,
    InstitutionListSerializer,
)
from rest_framework import serializers, status, generics
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
                                'id': 2,
                                'created_at': '2021-04-20T16:20:30.528668+02:00',
                                'entity_id': 'I41eovHQReGI_SG5KM6dSQ',
                                'issued_on': '2021-04-20T16:20:30.521307+02:00',
                                'award_type': 'requested',
                                'revoked': 'false',
                                'expires_at': '2030-04-20T16:20:30.521307+02:00',
                                'acceptance': 'Accepted',
                                'public': 'true',
                                'badgeclass': {
                                    'id': 3,
                                    'name': 'Edubadge account complete',
                                    'entity_id': 'nwsL-dHyQpmvOOKBscsN_A',
                                    'image_url': 'https://api-demo.edubadges.nl/media/uploads/badges/issuer_badgeclass_548517aa-cbab-4a7b-a971-55cdcce0e2a5.png',
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
                                'grade_achieved': '33',
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
                            'id': 2,
                            'created_at': '2021-04-20T16:20:30.528668+02:00',
                            'entity_id': 'I41eovHQReGI_SG5KM6dSQ',
                            'issued_on': '2021-04-20T16:20:30.521307+02:00',
                            'award_type': 'requested',
                            'revoked': 'false',
                            'expires_at': 'null',
                            'acceptance': 'Accepted',
                            'public': 'true',
                            'badgeclass': {
                                'id': 3,
                                'name': 'Edubadge account complete',
                                'entity_id': 'nwsL-dHyQpmvOOKBscsN_A',
                                'image': '/media/uploads/badges/issuer_badgeclass_548517aa-cbab-4a7b-a971-55cdcce0e2a5.png',
                                'description': '### Welcome to edubadges. Let your life long learning begin! ###\r\n\r\nYou are now ready to collect all your edubadges in your backpack. In your backpack you can store and manage them safely.\r\n\r\nShare them anytime you like and with whom you like.\r\n\r\nEdubadges are visual representations of your knowledge, skills and competences.',
                                'formal': 'false',
                                'participation': 'blended',
                                'assessment_type': 'written_exam',
                                'assessment_id_verified': 'false',
                                'assessment_supervised': 'false',
                                'quality_assurance_name': 'null',
                                'stackable': 'false',
                                'badgeclassextension_set': [
                                    {'name': 'extensions:LanguageExtension', 'value': 'en_EN'},
                                    {
                                        'name': 'extensions:LearningOutcomeExtension',
                                        'value': 'This is an edubadge for demonstration purposes. The learning outcome for this edubadge is:\n\n* you have a basic understanding of edubadges,\n* you have a basic understanding how to use eduID.\n',
                                    },
                                ],
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
                            'linkedin_url': 'https://www.linkedin.com/profile/add?startTask=CERTIFICATION_NAME&name=Edubadge%20account%20complete&organizationId=206815&issueYear=2021&issueMonth=3&certUrl=https%3A%2F%2Fdemo.edubadges.nl%2Fpublic%2Fassertions%2FI41eovHQReGI_SG5KM6dSQ&certId=I41eovHQReGI_SG5KM6dSQ&original_referer=https%3A%2F%2Fdemo.edubadges.nl',
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

    @extend_schema(
        methods=['PUT'],
        description='Update badge instance acceptance status and public visibility',
        parameters=[
            OpenApiParameter(
                name='entity_id',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description='entity_id of the badge instance',
            )
        ],
        request=inline_serializer(
            name='BadgeInstanceUpdateRequest',
            fields={
                'acceptance': serializers.CharField(required=False, help_text='Acceptance status of the badge'),
                'public': serializers.BooleanField(required=False, help_text='Whether the badge should be public'),
            },
        ),
        examples=[
            OpenApiExample(
                'Update Badge Instance Request',
                value={
                    'acceptance': 'Accepted',
                    'public': True,
                },
                description='Example request to update badge acceptance and public status',
                request_only=True,
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Badge instance updated successfully',
                response=BadgeInstanceDetailSerializer,
                examples=[
                    OpenApiExample(
                        'Updated Badge Instance',
                        value={
                            'id': 2,
                            'created_at': '2021-04-20T16:20:30.528668+02:00',
                            'entity_id': 'I41eovHQReGI_SG5KM6dSQ',
                            'issued_on': '2021-04-20T16:20:30.521307+02:00',
                            'award_type': 'requested',
                            'revoked': 'false',
                            'expires_at': 'null',
                            'acceptance': 'Accepted',
                            'public': 'true',
                            'badgeclass': {
                                'id': 3,
                                'name': 'Edubadge account complete',
                                'entity_id': 'nwsL-dHyQpmvOOKBscsN_A',
                                'image': '/media/uploads/badges/issuer_badgeclass_548517aa-cbab-4a7b-a971-55cdcce0e2a5.png',
                                'description': '### Welcome to edubadges. Let your life long learning begin! ###\r\n\r\nYou are now ready to collect all your edubadges in your backpack. In your backpack you can store and manage them safely.\r\n\r\nShare them anytime you like and with whom you like.\r\n\r\nEdubadges are visual representations of your knowledge, skills and competences.',
                                'formal': 'false',
                            },
                        },
                        description='Updated badge instance details',
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
            400: OpenApiResponse(
                description='Invalid request data',
                examples=[
                    OpenApiExample(
                        'Invalid Data',
                        value={'public': ['This field is required.']},
                        description='Validation errors in the request data',
                        response_only=True,
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def put(self, request, entity_id, **kwargs):
        instance = (
            BadgeInstance.objects.select_related('badgeclass')
            .select_related('badgeclass__issuer')
            .select_related('badgeclass__issuer__faculty')
            .select_related('badgeclass__issuer__faculty__institution')
            .filter(user=request.user)
            .filter(entity_id=entity_id)
            .get()
        )

        # Only allow updating acceptance and public fields
        acceptance = request.data.get('acceptance')
        public = request.data.get('public')

        # Validate acceptance field if provided
        if acceptance is not None:
            if acceptance not in ['Accepted', 'Unaccepted', 'Rejected']:
                return Response(
                    {'detail': 'Invalid acceptance value. Must be one of: Accepted, Unaccepted, Rejected'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # Only allow changing to 'Accepted' if currently not accepted
            if instance.acceptance in ['Unaccepted', 'Rejected'] and acceptance == 'Accepted':
                instance.acceptance = 'Accepted'

        # Update public field if provided
        if public is not None:
            instance.public = public

        instance.save()

        # Return the updated instance with full details
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
                                'id': 9606,
                                'created_at': '2026-01-23T16:19:08.699037+01:00',
                                'entity_id': 'Lgnh9njyStmGiI_w8396Xg',
                                'badgeclass': {
                                    'id': 113,
                                    'name': 'unclaimed test',
                                    'entity_id': 'X4MQyOYPS9yoMyZwZik1Jg',
                                    'image_url': 'https://api-demo.edubadges.nl/media/uploads/badges/issuer_badgeclass_32c9f91d-e731-40d4-99d4-c06ec6922f31.png',
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
                                'id': 40,
                                'entity_id': 'UMcx7xCPS4yBuztOj2IDEw',
                                'date_created': '2023-09-04T14:42:03.046498+02:00',
                                'denied': 'false',
                                'date_awarded': '2023-09-04T15:02:15.088536+02:00',
                                'badge_class': {
                                    'id': 119,
                                    'name': 'Test enrollment',
                                    'entity_id': '_KI6moSxQ3mAzPEfYUHnLg',
                                    'image_url': 'https://api-demo.edubadges.nl/media/uploads/badges/issuer_badgeclass_3b1a3c87-d7c6-488f-a1f9-1d3019a137ee.png',
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
            StudentsEnrolled.objects.select_related('badge_class')
            .prefetch_related('badge_class__badgeclassextension_set')
            .select_related('badge_class__issuer')
            .select_related('badge_class__issuer__faculty')
            .select_related('badge_class__issuer__faculty__institution')
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
                                'id': 9,
                                'created_at': '2025-10-07T12:41:36.332147+02:00',
                                'entity_id': 'lt3O3SUpS9Culz0IrA3rOg',
                                'badge_instances': [
                                    'badge-96-entity-id',
                                    'badge-175-entity-id',
                                    'badge-176-entity-id',
                                    'badge-287-entity-id',
                                ],
                                'name': 'Test collection 1',
                                'public': 'false',
                                'description': 'test',
                            },
                            {
                                'id': 11,
                                'created_at': '2025-10-27T16:14:42.650246+01:00',
                                'entity_id': 'dhuf6Qx2RMCtRKBw0iHGcg',
                                'badge_instances': ['badge-96-entity-id', 'badge-175-entity-id'],
                                'name': 'Test collection 2',
                                'public': 'true',
                                'description': 'Test2',
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
        collections = BadgeInstanceCollection.objects.filter(user=request.user).prefetch_related('badge_instances')
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
        description='Update an existing BadgeInstanceCollection by entity_id',
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


class CatalogBadgeClassListView(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CatalogBadgeClassSerializer
    filterset_class = CatalogBadgeClassFilter
    filter_backends = [DjangoFilterBackend]
    pagination_class = CatalogPagination

    @extend_schema(
        methods=['GET'],
        filters=True,
        description='Get a paginated list of badge classes. Supports filtering and page_size.',
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location='query',
                required=False,
                description='Page number for pagination',
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location='query',
                required=False,
                description='Number of items per page',
            ),
            OpenApiParameter(
                name='name',
                type=OpenApiTypes.STR,
                location='query',
                required=False,
                description='Filter badge classes by name',
            ),
            OpenApiParameter(
                name='institution',
                type=OpenApiTypes.STR,
                location='query',
                required=False,
                description='Filter badge classes by institution entity_id',
            ),
            OpenApiParameter(
                name='institution_type',
                location='query',
                required=False,
                description='Filter badge classes by institution_type (MBO/HBO/WO)',
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Paginated list of badge classes',
                response=CatalogBadgeClassSerializer(many=True),
                examples=[
                    OpenApiExample(
                        'Filtered and Paginated Badge Classes Example',
                        value={
                            'count': 124,
                            'next': 'https://api.example.com/catalog/badge-classes/?page=2&page_size=2&q=edubadge',
                            'previous': None,
                            'results': [
                                {
                                    'created_at': '2025-05-02T12:20:51.573423',
                                    'name': 'Edubadge account complete',
                                    'image': 'uploads/badges/edubadge_student.png',
                                    'archived': 0,
                                    'entity_id': 'qNGehQ2dRTKyjNtiDvhWsQ',
                                    'is_private': 0,
                                    'is_micro_credentials': 0,
                                    'badge_class_type': 'regular',
                                    'required_terms': {
                                        'entity_id': 'terms-123',
                                        'terms_type': 'FORMAL_BADGE',
                                        'institution': {
                                            'name_dutch': 'SURF',
                                            'name_english': 'SURF',
                                            'image_dutch': '',
                                            'image_english': '',
                                            'identifier': 'surf.nl',
                                            'alternative_identifier': None,
                                            'grondslag_formeel': 'gerechtvaardigd_belang',
                                            'grondslag_informeel': 'gerechtvaardigd_belang'
                                        },
                                        'terms_urls': [
                                            {
                                                'url': 'https://example.org/terms/nl',
                                                'language': 'nl',
                                                'excerpt': 'Door deel te nemen accepteer je...'
                                            },
                                            {
                                                'url': 'https://example.org/terms/en',
                                                'language': 'en',
                                                'excerpt': 'By participating you accept...'
                                            }
                                        ]
                                    },
                                    'user_has_accepted_terms': True,
                                    'issuer_name_english': 'Team edubadges',
                                    'issuer_name_dutch': 'Team edubadges',
                                    'issuer_entity_id': 'WOLxSjpWQouas1123Z809Q',
                                    'issuer_image_dutch': '',
                                    'issuer_image_english': 'uploads/issuers/surf.png',
                                    'faculty_name_english': 'eduBadges',
                                    'faculty_name_dutch': 'null',
                                    'faculty_entity_id': 'lVu1kbaqSDyJV_1Bu8_bcw',
                                    'faculty_image_dutch': '',
                                    'faculty_image_english': '',
                                    'faculty_on_behalf_of': 0,
                                    'faculty_type': 'null',
                                    'institution_name_english': 'SURF',
                                    'institution_name_dutch': 'SURF',
                                    'institution_entity_id': 'NiqkZiz2TaGT8B4RRwG8Fg',
                                    'institution_image_dutch': 'uploads/issuers/surf.png',
                                    'institution_image_english': 'uploads/issuers/surf.png',
                                    'institution_type': 'null',
                                    'self_requested_assertions_count': 1,
                                    'direct_awarded_assertions_count': 0,
                                },
                                {
                                    'created_at': '2025-05-02T12:20:57.914064',
                                    'name': 'Growth and Development',
                                    'image': 'uploads/badges/eduid.png',
                                    'archived': 0,
                                    'entity_id': 'Ge4D7gf1RLGYNZlSiCv-qA',
                                    'is_private': 0,
                                    'is_micro_credentials': 0,
                                    'badge_class_type': 'regular',
                                    'required_terms': {
                                        'entity_id': 'terms-123',
                                        'terms_type': 'FORMAL_BADGE',
                                        'institution': {
                                            'name_dutch': 'SURF',
                                            'name_english': 'SURF',
                                            'image_dutch': '',
                                            'image_english': '',
                                            'identifier': 'surf.nl',
                                            'alternative_identifier': None,
                                            'grondslag_formeel': 'gerechtvaardigd_belang',
                                            'grondslag_informeel': 'gerechtvaardigd_belang'
                                        },
                                        'terms_urls': [
                                            {
                                                'url': 'https://example.org/terms/nl',
                                                'language': 'nl',
                                                'excerpt': 'Door deel te nemen accepteer je...'
                                            },
                                            {
                                                'url': 'https://example.org/terms/en',
                                                'language': 'en',
                                                'excerpt': 'By participating you accept...'
                                            }
                                        ]
                                    },
                                    'user_has_accepted_terms': True,
                                    'issuer_name_english': 'Medicine',
                                    'issuer_name_dutch': 'null',
                                    'issuer_entity_id': 'yuflXDK8ROukQkxSPmh5ag',
                                    'issuer_image_dutch': '',
                                    'issuer_image_english': 'uploads/issuers/surf.png',
                                    'faculty_name_english': 'Medicine',
                                    'faculty_name_dutch': 'null',
                                    'faculty_entity_id': 'yYPphJ3bS5qszI7P69degA',
                                    'faculty_image_dutch': '',
                                    'faculty_image_english': '',
                                    'faculty_on_behalf_of': 0,
                                    'faculty_type': 'null',
                                    'institution_name_english': 'university-example.org',
                                    'institution_name_dutch': 'null',
                                    'institution_entity_id': '5rZhvRonT3OyyLQhhmuPmw',
                                    'institution_image_dutch': 'uploads/institution/surf.png',
                                    'institution_image_english': 'uploads/institution/surf.png',
                                    'institution_type': 'WO',
                                    'self_requested_assertions_count': 0,
                                    'direct_awarded_assertions_count': 0,
                                },
                            ],
                        },
                        response_only=True,
                    )
                ],
            ),
            500: OpenApiResponse(description='Internal server error occurred while retrieving badge classes.'),
        },
    )
    def get_queryset(self):
        return (
            BadgeClass.objects.select_related(
                'issuer',
                'issuer__faculty',
                'issuer__faculty__institution',
            )
            .prefetch_related(
                'issuer__faculty__institution__terms',
                'issuer__faculty__institution__terms__terms_urls',
            )
            .filter(
                is_private=False,
                issuer__archived=False,
                issuer__faculty__archived=False,
            )
            .exclude(issuer__faculty__visibility_type='TEST')
            .annotate(
                selfRequestedAssertionsCount=Count(
                    'badgeinstances',
                    filter=Q(badgeinstances__award_type='requested'),
                ),
                directAwardedAssertionsCount=Count(
                    'badgeinstances',
                    filter=Q(badgeinstances__award_type='direct_award'),
                ),
            )
        )


class UserProfileView(APIView):
    permission_classes = (IsAuthenticated, MobileAPIPermission)
    http_method_names = ('get', 'delete')

    @extend_schema(
        description="Get the authenticated user's profile",
        responses={200: UserProfileSerializer},
    )
    def get(self, request):
        serializer = UserProfileSerializer(
            request.user,
            context={'request': request},
        )
        return Response(serializer.data)

    @extend_schema(
        description='Delete the authenticated user',
        responses={
            204: OpenApiResponse(description='User account deleted successfully'),
            403: OpenApiResponse(description='Permission denied'),
        },
    )
    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgeClassDetailView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, MobileAPIPermission)
    lookup_field = 'entity_id'
    serializer_class = BadgeClassDetailSerializer
    queryset = BadgeClass.objects.select_related(
        'issuer',
        'issuer__faculty',
        'issuer__faculty__institution',
    ).prefetch_related(
        'badgeclassextension_set'
    )


class InstitutionListView(ListAPIView):
    permission_classes = (IsAuthenticated, MobileAPIPermission)
    serializer_class = InstitutionListSerializer

    def get_queryset(self):
        return (
            Institution.objects.filter(
                faculty__issuer__badgeclass__is_private=False,
                faculty__issuer__archived=False,
                faculty__archived=False,
                faculty__visibility_type='PUBLIC',
            ).distinct()
        )
