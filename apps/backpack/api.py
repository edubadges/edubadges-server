# encoding: utf-8

from backpack.models import BackpackBadgeShare
from backpack.serializers_v1 import LocalBadgeInstanceUploadSerializerV1
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    OpenApiTypes,
    extend_schema,
    inline_serializer,
)
from entity.api import BaseEntityDetailView
from issuer.models import BadgeClass, BadgeInstance, Issuer
from issuer.permissions import BadgrOAuthTokenHasScope, RecipientIdentifiersMatch
from mainsite.exceptions import BadgrApiException400
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from public.public_api import ImagePropertyDetailView
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_302_FOUND, HTTP_404_NOT_FOUND
from rest_framework.views import APIView

permission_denied_response = OpenApiResponse(
    response=inline_serializer(
        name="PermissionDeniedResponse",
        fields={"detail": serializers.CharField()},
    ),
    examples=[
        OpenApiExample(
            "Forbidden Response",
            value={"detail": "Authentication credentials were not provided."},
        )
    ],
)


class AwardIssuerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issuer
        fields = ["id", "entity_id", "name_dutch", "name_english", "image_dutch", "image_english", "faculty"]


class AwardBadgeClassSerializer(serializers.ModelSerializer):
    issuer = AwardIssuerSerializer(read_only=True)

    class Meta:
        model = BadgeClass
        fields = ["id", "entity_id", "name", "description", "criteria_text", "image", "issuer"]


class AwardSerializer(serializers.ModelSerializer):
    badgeclass = AwardBadgeClassSerializer(read_only=True)

    class Meta:
        model = BadgeInstance
        fields = [
            "id",
            "entity_id",
            "created_at",
            "issued_on",
            "award_type",
            "revoked",
            "expires_at",
            "acceptance",
            "public",
            "badgeclass",
            "grade_achieved",
            "include_grade_achieved",
        ]


class BackpackAwardDetail(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        methods=["GET"],
        description="Get a single badge instance by entity_id",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the badge instance",
            )
        ],
        responses={
            200: OpenApiResponse(
                description="Badge instance details",
                response=AwardSerializer(),
                examples=[
                    OpenApiExample(
                        "Badge Instance",
                        value={
                            "id": 2,
                            "created_at": "2021-04-20T16:20:30.528668+02:00",
                            "entity_id": "I41eovHQReGI_SG5KM6dSQ",
                            "issued_on": "2021-04-20T16:20:30.521307+02:00",
                            "award_type": "requested",
                            "revoked": "false",
                            "expires_at": "2030-04-20T16:20:30.521307+02:00",
                            "acceptance": "Accepted",
                            "public": "true",
                            "badgeclass": {
                                "id": 3,
                                "name": "Edubadge account complete",
                                "entity_id": "nwsL-dHyQpmvOOKBscsN_A",
                                "description": "Complete your account to start earning badges",
                                "criteria_text": "Register and verify your email address",
                                "image_url": "https://api-demo.edubadges.nl/media/uploads/badges/issuer_badgeclass_548517aa-cbab-4a7b-a971-55cdcce0e2a5.png",
                                "issuer": {
                                    "id": 1,
                                    "entity_id": "issuer-entity-id-123",
                                    "name_dutch": "SURF Edubadges",
                                    "name_english": "SURF Edubadges",
                                    "image_dutch": "null",
                                    "image_english": "/media/uploads/issuers/issuer_logo_ccd075bb-23cb-40b2-8780-b5a7eda9de1c.png",
                                    "faculty": {
                                        "name_dutch": "SURF",
                                        "name_english": "SURF",
                                        "image_dutch": "null",
                                        "image_english": "null",
                                        "on_behalf_of": "false",
                                        "on_behalf_of_display_name": "null",
                                        "on_behalf_of_url": "null",
                                        "institution": {
                                            "name_dutch": "University Voorbeeld",
                                            "name_english": "University Example",
                                            "image_dutch": "/media/uploads/institution/d0273589-2c7a-4834-8c35-fef4695f176a.png",
                                            "image_english": "/media/uploads/institution/eae5465f-98b1-4849-ac2d-47d4e1cd1252.png",
                                            "identifier": "university-example.org",
                                            "alternative_identifier": "university-example.org.tempguestidp.edubadges.nl",
                                            "grondslag_formeel": "gerechtvaardigd_belang",
                                            "grondslag_informeel": "gerechtvaardigd_belang",
                                        },
                                    },
                                },
                            },
                            "grade_achieved": "33",
                        },
                        description="Badge instance matching the provided entity_id",
                    ),
                ],
            ),
            404: OpenApiResponse(
                description="Badge instance not found",
                examples=[
                    OpenApiExample(
                        "Not Found",
                        value={"detail": "Badge instance not found"},
                        description="The requested badge instance does not exist or does not belong to the user",
                    ),
                ],
            ),
            403: permission_denied_response,
        },
    )
    def get(self, request, entity_id, **kwargs):
        instance = (
            BadgeInstance.objects.select_related("badgeclass")
            .select_related("badgeclass__issuer")
            .select_related("badgeclass__issuer__faculty")
            .select_related("badgeclass__issuer__faculty__institution")
            .filter(
                entity_id=entity_id,
                user=request.user,
                revoked=False,
            )
            .first()
        )

        if instance is None:
            return Response({"detail": "Badge instance not found"}, status=404)

        serializer = AwardSerializer(instance)
        return Response(serializer.data)


class BackpackAssertionDetail(BaseEntityDetailView):
    model = BadgeInstance
    v1_serializer_class = LocalBadgeInstanceUploadSerializerV1
    permission_classes = (AuthenticatedWithVerifiedEmail, RecipientIdentifiersMatch)
    http_method_names = ("delete", "put")

    @extend_schema(
        methods=["DELETE"],
        description="Reject terms",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the badge instance",
            )
        ],
    )
    def delete(self, request, **kwargs):
        """Remove an assertion from the backpack"""
        obj = self.get_object(request, **kwargs)
        obj.acceptance = BadgeInstance.ACCEPTANCE_REJECTED
        obj.public = False
        obj.save()
        return Response(status=HTTP_204_NO_CONTENT)

    @extend_schema(
        methods=["PUT"],
        description="Update acceptance of a BadgeInstance",
        parameters=[
            OpenApiParameter(
                name="entity_id",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                required=True,
                description="entity_id of the badge instance",
            )
        ],
        request=inline_serializer(
            name="AcceptTermsReject",
            fields={
                "acceptance": serializers.BooleanField(),
                "public": serializers.BooleanField(),
                "include_evidence": serializers.BooleanField(),
                "include_grade_achieved": serializers.BooleanField(),
            },
        ),
    )
    def put(self, request, **kwargs):
        """Update acceptance of an Assertion in the user's Backpack and make public / private"""
        fields_whitelist = ("acceptance", "public", "include_evidence", "include_grade_achieved")
        data = {k: v for k, v in list(request.data.items()) if k in fields_whitelist}
        return super(BackpackAssertionDetail, self).put(request, data=data, **kwargs)


class BackpackAssertionDetailImage(ImagePropertyDetailView, BadgrOAuthTokenHasScope):
    model = BadgeInstance
    prop = "image"
    valid_scopes = ["r:backpack", "rw:backpack"]


class ShareBackpackAssertion(BaseEntityDetailView):
    model = BadgeInstance
    permission_classes = (permissions.AllowAny,)  # this is AllowAny to support tracking sharing links in emails
    http_method_names = ("get",)

    def get(self, request, **kwargs):
        """
        Share a single badge to a support share provider
        ---
        parameters:
            - name: provider
              description: The identifier of the provider to use. Supports 'facebook', 'linkedin'
              required: true
              type: string
              paramType: query
        """
        # from recipient.api import _scrub_boolean
        redirect = request.query_params.get("redirect", "1")

        provider = request.query_params.get("provider")
        if not provider:
            raise BadgrApiException400("Unspecified share provider", 701)
        provider = provider.lower()

        source = request.query_params.get("source", "unknown")

        badge = self.get_object(request, **kwargs)
        if not badge:
            return Response(status=HTTP_404_NOT_FOUND)

        share = BackpackBadgeShare(provider=provider, badgeinstance=badge, source=source)
        share_url = share.get_share_url(provider)
        if not share_url:
            raise BadgrApiException400("Invalid share provider", 702)

        share.save()

        if redirect:
            headers = {"Location": share_url}
            return Response(status=HTTP_302_FOUND, headers=headers)
        else:
            return Response({"url": share_url})
