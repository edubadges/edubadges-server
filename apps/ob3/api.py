import logging
import uuid
from collections.abc import Sequence
from pprint import pformat
from typing import Optional

import badgrlog
from badgrsocialauth.utils import get_social_account
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from issuer.models import BadgeInstance
from mainsite.settings import (
    DEFAULT_DOMAIN,
    OB3_AGENT_AUTHZ_TOKEN_SPHEREON,
    OB3_AGENT_URL_SPHEREON,
    OB3_AGENT_URL_UNIME,
    OB3_AGENT_URL_VERAMO,
)
from rest_framework import permissions, status
from rest_framework.exceptions import AuthenticationFailed, NotFound, PermissionDenied, ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AchievementSubject, Credential, ImpierceOfferRequest, SphereonOfferRequest, VeramoOfferRequest
from .serializers import CredentialSerializer, VeramoOfferRequestSerializer

logger = logging.getLogger('django')


class CredentialsView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request: Request, **kwargs):
        _ = kwargs
        offer: Optional[str] = None
        offer_id = str(uuid.uuid4())
        badge_id = request.data.get('badge_id')  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        variant = request.data.get('variant')  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]

        if not request.user.is_authenticated:
            raise PermissionDenied('User must be authenticated')

        if not badge_id:
            raise ValidationError('Badge ID is required')

        badge_instance = self.__badge_instance(badge_id, request.user)
        logger.debug(f'Badge instance: {pformat(badge_instance.__dict__)}')

        if variant == 'authorization':
            credential = SphereonOfferRequest(
                offer_id,
                'OpenBadgeCredential',
                badge_instance,
                request.user.entity_id,  # TODO: how do we get an eduId?
                request.user.email,
                request.user.email,  # TODO: how do we get an eppn?
                request.user.last_name,
                request.user.first_name,
            )
            credential.set_url(OB3_AGENT_URL_SPHEREON)
            credential.set_authz_token(OB3_AGENT_AUTHZ_TOKEN_SPHEREON)
        elif variant == 'preauthorized':
            credential = ImpierceOfferRequest(offer_id, 'openbadge_credential', badge_instance)
            credential.set_url(OB3_AGENT_URL_UNIME)
        elif variant == 'veramo' or variant is None:
            # Get our Application URL, then find the callback url from apps.ob3.api_urls.py
            callback_url: str = DEFAULT_DOMAIN + reverse('ob3:callback')
            credential = VeramoOfferRequest('OpenBadgeCredential', badge_instance, callback_url)
            credential.set_url(OB3_AGENT_URL_VERAMO)
        else:
            raise ValidationError('Invalid variant')

        try:
            offer = credential.call()
            logger.debug(f'Offer: {offer}')
        except Exception as error:
            raise ValidationError(str(error))

        logger.info(f'Issued credential for badge {badge_id} with offer_id {offer_id}')

        badgr_logger = badgrlog.BadgrLogger()
        badgr_logger.event(badgrlog.CredentialIssuedEvent(badge_instance, request.user, offer_id, variant))

        return Response({'offer': offer}, status=status.HTTP_201_CREATED)

    def __badge_instance(self, badge_id, user) -> BadgeInstance:
        try:
            return BadgeInstance.objects.get(id=badge_id, user=user)
        except ObjectDoesNotExist:
            raise NotFound(f'Badge instance with id {badge_id} not found')


class OB3CallbackView(APIView):
    permission_classes: tuple[type[permissions.BasePermission]] = (permissions.AllowAny,)
    http_method_names: Sequence[str] = ['post']

    def post(self, request: Request):
        entity_id, social_uuid = self.__parse_body(request)
        badge_instance = self.__get_badge_instance(entity_id)

        self.__authorize(badge_instance, social_uuid)

        credential = self.__create_credential(badge_instance)
        serializer = CredentialSerializer(credential)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def __parse_body(self, request: Request) -> tuple[str, str]:
        state = request.data.get('state')  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]
        user_id = request.data.get('user_id')  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportUnknownVariableType]

        if not isinstance(state, str) or not state:
            raise ValidationError('state parameter is required')

        if not isinstance(user_id, str) or not user_id:
            raise ValidationError('user_id parameter is required')

        return state, user_id

    def __authorize(self, badge_instance: BadgeInstance, social_uuid: str):
        # Verify that the badge instance was issued to the user associated with the provided social account UUID
        social_account = get_social_account(social_uuid)
        if not social_account:
            raise AuthenticationFailed('Invalid user')

        if social_account.user_id != badge_instance.user_id:  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue] We need django-stubs first
            raise PermissionDenied('Invalid user')

    def __get_badge_instance(self, entity_id: str) -> BadgeInstance:
        try:
            return BadgeInstance.objects.get(entity_id=entity_id)
        except ObjectDoesNotExist:
            raise NotFound

    def __create_credential(self, badge_instance: BadgeInstance) -> Credential:
        credential_subject = AchievementSubject.from_badge_instance(badge_instance)
        credential = Credential(
            entity_id=badge_instance.entity_id,
            issuer=badge_instance.badgeclass.issuer,
            valid_from=badge_instance.issued_on,
            credential_subject=credential_subject,
        )

        if badge_instance.expires_at:
            credential.valid_until = badge_instance.expires_at

        return credential
