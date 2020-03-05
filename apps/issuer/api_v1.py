# encoding: utf-8

from json import dumps as json_dumps
from json import loads as json_loads

import badgrlog
from apispec_drf.decorators import apispec_list_operation, apispec_operation
from badgeuser.models import CachedEmailAddress, BadgeUser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing
from entity.api import VersionedObjectMixin
from issuer.models import Issuer, IssuerStaff
from issuer.permissions import IsOwnerOrStaff
from issuer.serializers_v1 import BadgeClassSerializerV1, IssuerRoleActionSerializerV1, IssuerStaffSerializerV1
from issuer.utils import get_badgeclass_by_identifier
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker
from rest_framework import status, authentication, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

logger = badgrlog.BadgrLogger()


class AbstractIssuerAPIEndpoint(APIView):
    authentication_classes = (
        authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    def get_object(self, slug, queryset=None):
        """ Ensure user has permissions on Issuer """

        queryset = queryset if queryset is not None else self.queryset
        try:
            obj = queryset.get(entity_id=slug)
        except self.model.DoesNotExist:
            return None

        try:
            self.check_object_permissions(self.request, obj)
        except PermissionDenied:
            return None
        else:
            return obj

    def get_list(self, slug=None, queryset=None, related=None):
        """ Ensure user has permissions on Issuer, and return badgeclass queryset if so. """
        queryset = queryset if queryset is not None else self.queryset

        obj = queryset
        if slug is not None:
            obj = queryset.filter(slug=slug)
        if related is not None:
            obj = queryset.select_related(related)

        if not obj.exists():
            return self.model.objects.none()

        try:
            self.check_object_permissions(self.request, obj[0])
        except PermissionDenied:
            return self.model.objects.none()
        else:
            return obj


class FindBadgeClassDetail(APIView):
    """
    GET a specific BadgeClass by searching by identifier
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)

    @apispec_operation(
        summary="Get a specific BadgeClass by searching by identifier",
        tags=['BadgeClasses'],
        parameters=[
            {
                "in": "query",
                "name": "identifier",
                'required': True,
                "description": "The identifier of the badge possible values: JSONld identifier, BadgeClass.id, or BadgeClass.slug"
            }
        ]
    )
    def get(self, request, **kwargs):
        identifier = request.query_params.get('identifier')
        badge = get_badgeclass_by_identifier(identifier)
        if badge is None:
            raise NotFound("No BadgeClass found by identifier: {}".format(identifier))

        serializer = BadgeClassSerializerV1(badge)
        return Response(serializer.data)

