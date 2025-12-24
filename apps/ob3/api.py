import logging
import uuid
from pprint import pformat
from typing import Optional, Sequence
from urllib.parse import urljoin

from django.contrib.auth.models import Permission

import badgrlog
import requests
from django.core.exceptions import BadRequest, ObjectDoesNotExist
from django.http import Http404
from issuer.models import BadgeInstance
from mainsite.settings import OB3_AGENT_AUTHZ_TOKEN_SPHEREON, OB3_AGENT_URL_SPHEREON, OB3_AGENT_URL_UNIME
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AchievementSubject, Credential, ImpierceOfferRequest, SphereonOfferRequest
from .serializers import CredentialSerializer, ImpierceOfferRequestSerializer, SphereonOfferRequestSerializer

logger = logging.getLogger('django')


class CredentialsView(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['post']

    def post(self, request, **_kwargs):
        _ = _kwargs  # explicitly ignore kwargs

        offer: Optional[str] = None
        offer_id = str(uuid.uuid4())
        badge_id = request.data.get('badge_id')
        variant = request.data.get('variant')

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
            serializer = SphereonOfferRequestSerializer(credential)
            logger.debug(f'Credential: {pformat(serializer.data)}')
            offer = self.__issue_sphereon_badge(serializer.data)
            logger.debug(f'Sphereon offer: {offer}')
        elif variant == 'preauthorized':
            credential = ImpierceOfferRequest(offer_id, 'openbadge_credential', badge_instance)
            serializer = ImpierceOfferRequestSerializer(credential)
            logger.debug(f'Credential: {pformat(serializer.data)}')
            self.__issue_unime_badge(serializer.data)
            offer = self.__get_unime_offer(offer_id)
            logger.debug(f'Unime offer: {offer}')

        logger.info(f'Issued credential for badge {badge_id} with offer_id {offer_id}')

        # Log the credential issuance event
        badgr_logger = badgrlog.BadgrLogger()
        badgr_logger.event(badgrlog.CredentialIssuedEvent(badge_instance, request.user, offer_id, variant))

        return Response({'offer': offer}, status=status.HTTP_201_CREATED)

    def __badge_instance(self, badge_id, user) -> BadgeInstance:
        try:
            return BadgeInstance.objects.get(id=badge_id, user=user)
        except ObjectDoesNotExist:
            raise Http404

    def __issue_sphereon_badge(self, credential_offer_request) -> str:
        logger.debug(f'Requesting credential issuance: {OB3_AGENT_URL_SPHEREON} {credential_offer_request}')
        response = requests.post(
            timeout=5,
            url=OB3_AGENT_URL_SPHEREON,
            json=credential_offer_request,
            headers={'Accept': 'application/json', 'Authorization': f'Bearer {OB3_AGENT_AUTHZ_TOKEN_SPHEREON}'},
        )
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to issue badge:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise BadRequest(msg)

        return response.text

    def __issue_unime_badge(self, credential) -> str:
        url = urljoin(OB3_AGENT_URL_UNIME, 'credentials')
        headers = {'Accept': 'application/json'}
        payload = credential

        logger.debug(f'Requesting credential issuance: {url} {headers} {payload}')
        response = requests.post(timeout=5, json=payload, url=url, headers=headers)
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to issue badge:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise BadRequest(msg)

        return response.text

    def __get_unime_offer(self, offer_id: str) -> str:
        url = urljoin(OB3_AGENT_URL_UNIME, 'offers')
        headers = {'Accept': 'application/json'}
        payload = {'offerId': offer_id}

        logger.debug(f'Requesting offer: {url} {headers} {payload}')
        response = requests.post(timeout=5, url=url, json=payload, headers=headers)
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to get offer:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise BadRequest(msg)

        return response.text


class OB3CallbackView(APIView):
    permission_classes: tuple[type[permissions.BasePermission]] = (permissions.AllowAny,)
    http_method_names: Sequence[str]  = ['post']

    def post(self, _, entity_id: str):
        badge_instance = self.__get_badge_instance(entity_id)
        credential = self.__create_credential(badge_instance)
        serializer = CredentialSerializer(credential)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def __get_badge_instance(self, entity_id: str) -> BadgeInstance:
        try:
            return BadgeInstance.objects.get(entity_id=entity_id)
        except ObjectDoesNotExist:
            raise Http404

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
