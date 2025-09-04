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
from directaward.models import DirectAward, DirectAwardBundle
from issuer.models import BadgeInstance, BadgeInstanceCollection
from issuer.serializers import BadgeInstanceCollectionSerializer
from lti_edu.models import StudentsEnrolled
from mainsite.exceptions import BadgrApiException400
from mainsite.mobile_api_authentication import TemporaryUser
from mainsite.permissions import MobileAPIPermission
from mobile_api.serializers import BadgeInstanceDetailSerializer, DirectAwardSerializer, StudentsEnrolledSerializer, \
    StudentsEnrolledDetailSerializer, BadgeCollectionSerializer
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
        examples=[],
    )
    def get(self, request, **kwargs):
        logger = logging.getLogger('Badgr.Debug')

        user = request.user
        '''
        Check if the user is known, has agreed to the terms and has a validated_name. If the user is not known
        then check if there is a validate name and provision the user. If all is well, then return the user information
        '''
        if isinstance(user, TemporaryUser):
            # Check if there is a validated name
            headers = {
                'Accept': 'application/json, application/json;charset=UTF-8',
                'Authorization': f'Bearer {user.bearer_token}',
            }
            response = requests.get(f'{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links', headers=headers,
                                    timeout=60)
            if response.status_code != 200:
                error = f'Server error: eduID eppn endpoint error ({response.status_code})'
                logger.debug(error)
                return Response({"error": str(error)})

            eppn_json = response.json()
            for info in eppn_json:
                if 'eppn' in info and 'schac_home_organization' in info:
                    request.user.add_affiliations(
                        [
                            {
                                'eppn': info['eppn'].lower(),
                                'schac_home': info['schac_home_organization'],
                            }
                        ]
                    )
                    logger.info(f'Stored affiliations {info["eppn"]} {info["schac_home_organization"]}')
            validated_names = [info['validated_name'] for info in eppn_json if 'validated_name' in info]
            if request.user.validated_name and len(validated_names) == 0:
                ret = HttpResponseRedirect(ret.url + '&revalidate-name=true')
            if len(validated_names) > 0:
                # Use the preferred linked account for the validated_name.
                preferred_validated_name = [info['validated_name'] for info in eppn_json if info['preferred']]
                if not preferred_validated_name:
                    # This should never happen as it would be a bug in eduID, but let's be defensive
                    preferred_validated_name = [validated_names[0]]
                val_name_audit_trail_signal.send(
                    sender=request.user.__class__,
                    user=request.user,
                    old_validated_name=request.user.validated_name,
                    new_validated_name=preferred_validated_name[0],
                )
                request.user.validated_name = preferred_validated_name[0]
            else:
                val_name_audit_trail_signal.send(
                    sender=request.user.__class__,
                    user=request.user,
                    old_validated_name=request.user.validated_name,
                    new_validated_name=None,
                )
                request.user.validated_name = None
            request.user.save()

        return Response(data)




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
        data = serializer.data
        return Response(data)


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
        data = serializer.data
        return Response(data)


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
        data = serializer.data
        return Response(data)


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
        data = serializer.data
        return Response(data)


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
        data = serializer.data
        return Response(data)

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
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related
        collections = BadgeInstanceCollection.objects \
            .filter(user=request.user)
        serializer = BadgeCollectionSerializer(collections, many=True)
        data = serializer.data
        return Response(data)

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
