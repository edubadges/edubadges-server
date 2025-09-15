import logging

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter, \
    OpenApiTypes
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Subquery
from rest_framework import status
from badgeuser.models import StudentAffiliation
from badgrsocialauth.providers.eduid.provider import EduIDProvider
from directaward.models import DirectAward, DirectAwardBundle
from issuer.models import BadgeInstance, BadgeInstanceCollection
from issuer.serializers import BadgeInstanceCollectionSerializer
from lti_edu.models import StudentsEnrolled
from mainsite.exceptions import BadgrApiException400
from mainsite.mobile_api_authentication import TemporaryUser
from mainsite.permissions import MobileAPIPermission
from mobile_api.helper import process_eduid_response, RevalidatedNameException, NoValidatedNameException
from mobile_api.serializers import BadgeInstanceDetailSerializer, DirectAwardSerializer, StudentsEnrolledSerializer, \
    StudentsEnrolledDetailSerializer, BadgeCollectionSerializer, UserSerializer
from mobile_api.serializers import BadgeInstanceSerializer
import requests
from django.conf import settings

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
            200: OpenApiResponse(
                description="Successful responses with examples",
                response=dict,  # or your serializer class
                examples=[
                    OpenApiExample(
                        "User needs to link account in eduID",
                        value={"status": "link-account"},
                        description="Redirect the user back to eduID with 'acr_values' = 'https://eduid.nl/trust/validate-names'",
                        response_only=True,
                    ),
                    OpenApiExample(
                        "User needs to revalidate name in eduID",
                        value={"status": "revalidate-name"},
                        description="Redirect the user back to eduID with 'acr_values' = 'https://eduid.nl/trust/validate-names'",
                        response_only=True,
                    ),
                    OpenApiExample(
                        "User needs to agree to terms",
                        value={"email": "jdoe@example.com", "last_name": "Doe", "first_name": "John",
                                "validated_name": "John Doe", "schac_homes": ["university-example.org"],
                                "terms_agreed": False,
                                "termsagreement_set": []},
                        description="Show the terms and use the 'accept-general-terms' endpoint",
                        response_only=True,
                    ),
                    OpenApiExample(
                        "User valid",
                        value={"email": "jdoe@example.com", "last_name": "Doe", "first_name": "John",
                                "validated_name": "John Doe", "schac_homes": ["university-example.org"],
                                "terms_agreed": True, "termsagreement_set": [{"agreed": True, "agreed_version": 1,
                                                                              "terms": {
                                                                                  "terms_type": "service_agreement_student"}
                                                                              }, {"agreed": True, "agreed_version": 1,
                                                                                  "terms": {
                                                                                      "terms_type": "terms_of_service",
                                                                                      "institution": None}}]},
                        description="The user is valid, proceed with fetching all badge-instances and OPEN direct-awards",
                        response_only=True,
                    ),
                ],
            )
        }
    )
    def get(self, request, **kwargs):
        logger = logging.getLogger('Badgr.Debug')

        user = request.user
        results = {}
        '''
        Check if the user is known, has agreed to the terms and has a validated_name. If the user is not known
        then check if there is a validate name and provision the user. If all is well, then return the user information
        '''
        temporary_user = isinstance(user, TemporaryUser)
        if temporary_user:
            bearer_token = user.bearer_token
        else:
            authorization = request.environ.get('HTTP_AUTHORIZATION')
            bearer_token = authorization[len('bearer '):]

        headers = {
            'Accept': 'application/json, application/json;charset=UTF-8',
            'Authorization': f'Bearer {bearer_token}',
        }
        url = f"{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links"
        response = requests.get(url, headers=headers,
                                timeout=60)
        if response.status_code != 200:
            error = f'Server error: eduID eppn endpoint error ({response.status_code})'
            logger.debug(error)
            return Response(data={"error": str(error)}, status=response.status_code)

        eduid_response = response.json()
        validated_names = [info['validated_name'] for info in eduid_response if 'validated_name' in info]
        if not validated_names:
            # The user must go back to eduID and link an account
            results["status"] = "link-account"
            return Response(data=results)
        if temporary_user:
            # User must be created / provisioned together with social account
            provider = EduIDProvider(request)
            social_login = provider.sociallogin_from_response(request, user.user_payload)
            social_login.save(request)
            user = social_login.user
        try:
            process_eduid_response(eduid_response, user)
        except RevalidatedNameException:
            results["status"] = "revalidate-name"
            return Response(data=results)
        except NoValidatedNameException:
            results["status"] = "link-account"
            return Response(data=results)

        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data)


class AcceptGeneralTerms(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Accept the general terms',
        examples=[],
    )
    def get(self, request, **kwargs):
        logger = logging.getLogger('Badgr.Debug')
        user = request.user
        user.accept_general_terms()
        user.save()
        logger.info(f"Accepted general terms for user {user.email}")
        return Response(data={"status": "ok"})


class BadgeInstances(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all assertions for the user',
        examples=[],
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related

        instances = BadgeInstance.objects \
            .select_related("badgeclass") \
            .select_related("badgeclass__issuer") \
            .select_related("badgeclass__issuer__faculty") \
            .select_related("badgeclass__issuer__faculty__institution") \
            .filter(user=request.user)
        serializer = BadgeInstanceSerializer(instances, many=True)
        return Response(serializer.data)


class BadgeInstanceDetail(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get badge details for the user',
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the badge instance"
            )
        ],
        examples=[],
    )
    def get(self, request, entity_id, **kwargs):
        instance = BadgeInstance.objects \
            .select_related("badgeclass") \
            .prefetch_related("badgeclass__badgeclassextension_set") \
            .select_related("badgeclass__issuer") \
            .select_related("badgeclass__issuer__faculty") \
            .select_related("badgeclass__issuer__faculty__institution") \
            .filter(user=request.user) \
            .filter(entity_id=entity_id) \
            .get()
        serializer = BadgeInstanceDetailSerializer(instance)
        return Response(serializer.data)


class UnclaimedDirectAwards(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all unclaimed awarded badges for the user',
        examples=[],
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related
        affiliations = StudentAffiliation.objects.filter(user=request.user)

        direct_awards = DirectAward.objects \
            .select_related("badgeclass") \
            .select_related("badgeclass__issuer") \
            .select_related("badgeclass__issuer__faculty") \
            .select_related("badgeclass__issuer__faculty__institution") \
            .filter(
            Q(eppn__in=Subquery(affiliations.values("eppn"))) |
            Q(recipient_email=request.user.email,
              bundle__identifier_type=DirectAwardBundle.IDENTIFIER_EMAIL)) \
            .filter(status='Unaccepted')

        serializer = DirectAwardSerializer(direct_awards, many=True)
        return Response(serializer.data)


class Enrollments(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all enrollments for the user',
        examples=[],
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related
        enrollments = StudentsEnrolled.objects \
            .select_related("badge_class") \
            .select_related("badge_class__issuer") \
            .select_related("badge_class__issuer__faculty") \
            .select_related("badge_class__issuer__faculty__institution") \
            .filter(user=request.user)

        serializer = StudentsEnrolledSerializer(enrollments, many=True)
        return Response(serializer.data)


class EnrollmentDetail(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get enrollment details for the user',
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the enrollment"
            )
        ],
        examples=[],
    )
    # ForeignKey / OneToOneField → select_related
    # ManyToManyField / reverse FK → prefetch_related
    def get(self, request, entity_id, **kwargs):
        enrollment = StudentsEnrolled.objects \
            .select_related("badgeclass") \
            .prefetch_related("badgeclass__badgeclassextension_set") \
            .select_related("badgeclass__issuer") \
            .select_related("badgeclass__issuer__faculty") \
            .select_related("badgeclass__issuer__faculty__institution") \
            .filter(user=request.user) \
            .filter(entity_id=entity_id) \
            .get()
        serializer = StudentsEnrolledDetailSerializer(enrollment)
        return Response(serializer.data)

    @extend_schema(
        methods=['DELETE'],
        description='Delete enrollment for the user',
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the enrollment"
            )
        ],
        examples=[],
    )
    def delete(self, request, entity_id, **kwargs):
        enrollment = get_object_or_404(StudentsEnrolled, user=request.user, entity_id=entity_id)
        if enrollment.date_awarded:
            raise BadgrApiException400("Awarded enrollments cannot be withdrawn", 206)
        enrollment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BadgeCollectionsListView(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all badge collections for the user',
        examples=[],
    )
    def get(self, request, **kwargs):
        collections = BadgeInstanceCollection.objects \
            .filter(user=request.user)
        serializer = BadgeCollectionSerializer(collections, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=BadgeInstanceCollectionSerializer,
        responses=BadgeInstanceCollectionSerializer,
        description="Create a new BadgeInstanceCollection",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the enrollment"
            )
        ],
    )
    def post(self, request):
        serializer = BadgeInstanceCollectionSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        badge_collection = serializer.save()
        return Response(BadgeInstanceCollectionSerializer(badge_collection).data, status=status.HTTP_201_CREATED)


class BadgeCollectionsDetailView(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        request=BadgeInstanceCollectionSerializer,
        responses=BadgeInstanceCollectionSerializer,
        description="Update an existing BadgeInstanceCollection by ID",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the enrollment"
            )
        ],
    )
    def put(self, request, entity_id):
        badge_collection = get_object_or_404(BadgeInstanceCollection, user=request.user, entity_id=entity_id)
        serializer = BadgeInstanceCollectionSerializer(badge_collection, data=request.data,
                                                       context={"request": request}, partial=False)
        if serializer.is_valid():
            badge_collection = serializer.save()
            return Response(BadgeInstanceCollectionSerializer(badge_collection).data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        request=None,
        responses={204: None},
        description="Delete a BadgeInstanceCollection by ID",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the enrollment"
            )
        ],
    )
    def delete(self, request, entity_id):
        badge_collection = get_object_or_404(BadgeInstanceCollection, entity_id=entity_id, user=request.user)
        badge_collection.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
