from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from issuer.models import BadgeInstance
from mainsite.permissions import MobileAPIPermission
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter, \
    OpenApiTypes

from mobile_api.serializers import BadgeInstanceSerializer, BadgeInstanceDetailSerializer
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter, \
    OpenApiTypes
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.models import BadgeInstance
from mainsite.permissions import MobileAPIPermission
from mobile_api.serializers import BadgeInstanceSerializer

permission_denied_response = OpenApiResponse(
    response=inline_serializer(name='PermissionDeniedResponse', fields={'detail': serializers.CharField()}),
    examples=[
        OpenApiExample(name='Forbidden Response', value={'detail': 'Authentication credentials were not provided.'})
    ],
)


class BadgeInstances(APIView):
    permission_classes = (MobileAPIPermission,)

    @extend_schema(
        methods=['GET'],
        description='Get all awarded badges for the user',
        parameters=[
            OpenApiParameter(
                name="x-requested-with",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="x-requested-with header, must be mobile",
                examples=[
                    OpenApiExample(
                        name="mobile",
                        value="mobile"
                    )
                ]
            )
        ],
        examples=[],
    )
    def get(self, request, **kwargs):
        # ForeignKey / OneToOneField → select_related
        # ManyToManyField / reverse FK → prefetch_related

        instances = BadgeInstance.objects \
            .select_related("badgeclass") \
            .prefetch_related("badgeclass__badgeclassextension_set") \
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
        description='Get awarded badge details for the user',
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the badge instance"
            ),
            OpenApiParameter(
                name="x-requested-with",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                description="x-requested-with header, must be mobile",
                examples=[
                    OpenApiExample(
                        name="mobile",
                        value="mobile"
                    )
                ]
            )
        ],
        examples=[],
    )
    def get(self, request, **kwargs):
        entity_id = kwargs.get('entity_id', None)
        instance = BadgeInstance.objects \
            .select_related("badgeclass") \
            .prefetch_related("badgeclass__badgeclassextension_set") \
            .select_related("badgeclass__issuer") \
            .select_related("badgeclass__issuer__faculty") \
            .select_related("badgeclass__issuer__faculty__institution") \
            .filter(user=request.user)\
            .filter(entity_id=entity_id)\
            .get()
        serializer = BadgeInstanceDetailSerializer(instance)
        data = serializer.data
        return Response(data)
