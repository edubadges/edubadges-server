from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from mainsite.permissions import MobileAPIPermission
from drf_spectacular.utils import extend_schema, inline_serializer, OpenApiExample, OpenApiResponse, OpenApiParameter, \
    OpenApiTypes

permission_denied_response = OpenApiResponse(
    response=inline_serializer(name='PermissionDeniedResponse', fields={'detail': serializers.CharField()}),
    examples=[
        OpenApiExample(name='Forbidden Response', value={'detail': 'Authentication credentials were not provided.'})
    ],
)


def dict_fetch_all(cursor):
    desc = cursor.description
    rows = cursor.fetchall()
    res = [dict(zip([col[0] for col in desc], row)) for row in rows]
    return res


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
                        name="header",
                        value="mobile"
                    )
                ]
            )
        ],
        responses={
            200: inline_serializer(
                name='BadgeInstancesResponse',
                fields={
                    'rejected': serializers.BooleanField(),
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
        },
        examples=[],
    )
    def get(self, request, **kwargs):
        return Response({"res": "Ok"}, status=status.HTTP_200_OK)
