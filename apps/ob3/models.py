# Description: This file contains the models for the badge-issuing service.

import logging
from hashlib import sha256
from typing import Optional
from urllib.parse import urljoin

import requests
from issuer.models import BadgeInstance
from ob3.serializers import ImpierceOfferRequestSerializer, SphereonOfferRequestSerializer, VeramoOfferRequestSerializer
from typing_extensions import override

logger = logging.getLogger('django')


def generate_sha256_hashstring(identifier: str, salt: Optional[str] = None):
    """
    Generate a SHA-256 hash string from an identifier and salt.
    This is now exactly the same as the one in issuer/utils, but that's accidental
    similarity. OBv3 can (will?) have its own variant of this function.

    Args:
        identifier: The identifier to hash
        salt: An optional salt to add to the identifier

    Returns:
        A SHA-256 hash string
    """
    key = '{}{}'.format(identifier.lower(), salt if salt is not None else '')
    return 'sha256$' + sha256(key.encode('utf-8')).hexdigest()


# Mixin to provide dynamic field assignment to a class
class StructFieldsMixin:
    FIELDS = []

    def __init__(self, **kwargs):
        """
        Initialize the course with dynamic field assignment.
        Fields are validated against FIELDS class variable.

        Args:
            **kwargs: Keyword arguments corresponding to FIELDS

        Raises:
            ValueError: If any provided field is not in FIELDS or if any field
                        is missing
        """
        # Check for invalid fields
        invalid_fields = set(kwargs.keys()) - set(self.FIELDS)
        if invalid_fields:
            raise ValueError(f'Invalid fields provided: {invalid_fields}')

        # Check for missing fields
        missing_fields = set(self.FIELDS) - set(kwargs.keys())
        if missing_fields:
            raise ValueError(f'Missing required fields: {missing_fields}')

        for field in self.FIELDS:
            setattr(self, field, kwargs.get(field, None))
        for key, value in kwargs.items():
            setattr(self, key, value)


# Base class for all offer requests
class OfferRequest:
    _url: Optional[str] = None
    _authz_token: Optional[str] = None

    def call(self) -> str:
        """
        Generic method to make HTTP calls to issue credentials.
        This base implementation does nothing - subclasses should override.
        Returns:
            The response text from the HTTP call
        """
        return 'invalid offer request called'

    def _get_url(self) -> str:
        if not self._url:
            raise ValueError('URL is not set')
        return self._url

    def set_url(self, url: str):
        self._url = url

    def _get_authz_token(self) -> Optional[str]:
        return self._authz_token

    def set_authz_token(self, authz_token: str):
        self._authz_token = authz_token


# A plain old Python object (POPO) that represents an educational credential
class ImpierceOfferRequest(OfferRequest):
    def __init__(self, offer_id, credential_configuration_id, badge_instance):
        self.offer_id = offer_id
        self.credential_configuration_id = credential_configuration_id

        credential_subject = AchievementSubject.from_badge_instance(badge_instance)
        self.credential = Credential(
            entity_id=badge_instance.entity_id,
            issuer=badge_instance.badgeclass.issuer,
            valid_from=badge_instance.issued_on,
            credential_subject=credential_subject,
        )

        if badge_instance.expires_at:
            self.expires_at = badge_instance.expires_at.strftime('%Y-%m-%dT%H:%M:%SZ')
            self.credential.valid_until = badge_instance.expires_at
        else:
            self.expires_at = 'never'

    @override
    def call(self) -> str:
        """
        Issue the credential and get the offer for Impierce (Unime).
        Returns:
            The offer ID as a string
        """
        # First, issue the credential
        self.__issue_unime_badge()

        # Then get the offer
        return self.__get_unime_offer()

    def __issue_unime_badge(self) -> None:
        """Issue the credential to Unime API."""
        url = urljoin(self._get_url(), 'credentials')
        headers = {'Accept': 'application/json'}
        payload = ImpierceOfferRequestSerializer(self).data

        logger.debug(f'Requesting credential issuance: {url} {headers} {payload}')
        response = requests.post(timeout=5, json=payload, url=url, headers=headers)
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to issue badge:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise Exception(msg)

    def __get_unime_offer(self) -> str:
        """Get the offer from Unime API."""
        url = urljoin(self._get_url(), 'offers')
        headers = {'Accept': 'application/json'}
        payload = {'offerId': self.offer_id}

        logger.debug(f'Requesting offer: {url} {headers} {payload}')
        response = requests.post(timeout=5, url=url, json=payload, headers=headers)
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to get offer:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise Exception(msg)

        return response.text


class SphereonOfferRequest(OfferRequest):
    def __init__(
        self, offer_id, credential_configuration_id, badge_instance, edu_id, email, eppn, family_name, given_name
    ):
        self.credential_configuration_ids = [credential_configuration_id]
        self.grants = {
            'authorization_code': {
                'issuer_state': offer_id,
            }
        }
        credential_subject = AchievementSubject.from_badge_instance(badge_instance)
        self.credential = Credential(
            entity_id=badge_instance.entity_id,
            issuer=badge_instance.badgeclass.issuer,
            valid_from=badge_instance.issued_on,
            credential_subject=credential_subject,
        )
        # TODO: Sphereon doesn't seem to support expiration dates yet, so we don't set it here.

        self.edu_id = edu_id
        self.email = email
        self.eppn = eppn
        self.family_name = family_name
        self.given_name = given_name

    @override
    def call(self):
        """
        Issue the credential for Sphereon.
        Returns:
            The response text from the HTTP call
        """
        headers = {'Accept': 'application/json'}
        if self._get_authz_token():
            headers['Authorization'] = f'Bearer {self._get_authz_token()}'

        payload = SphereonOfferRequestSerializer(self).data

        url = self._get_url()
        logger.debug(f'Requesting credential issuance: {url} {payload}')
        response = requests.post(
            timeout=5,
            url=url,
            json=payload,
            headers=headers,
        )
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to issue badge:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise Exception(msg)

        return response.text


class VeramoOfferRequest(OfferRequest):
    """
    A Veramo offer request that doesn't send the initial credential payload.
    This is used for the /api/create-offer endpoint.
    """

    def __init__(self, credential_configuration_id: str, badge_instance: BadgeInstance, callback_url: str):
        self.credentials: list[str] = [credential_configuration_id]
        self.grants: dict[str, dict[str, str]] = {'authorization_code': {'issuer_state': badge_instance.entity_id}}
        self.callback_url: str = callback_url

    @override
    def call(self) -> str:
        """
        Create an offer for the credential.
        Returns:
            The response text from the HTTP call containing the offer URI
        """
        headers = {'Accept': 'application/json'}
        if self._get_authz_token():
            headers['Authorization'] = f'Bearer {self._get_authz_token()}'

        payload = VeramoOfferRequestSerializer(self).data

        url = self._get_url()
        logger.debug(f'Requesting offer creation: {url} {headers} {payload}')
        response = requests.post(timeout=5, json=payload, url=url, headers=headers)
        logger.debug(f'Response: {response.status_code} {response.text}')

        if response.status_code >= 400:
            msg = f'Failed to create offer:\n\tcode: {response.status_code}\n\tcontent:\n {response.text}'
            raise Exception(msg)

        offer_uri = str(response.json()['uri'])
        logger.debug(f'Offer URI: {offer_uri}')

        return offer_uri


class Credential:
    def __init__(self, entity_id, issuer, valid_from, credential_subject, **kwargs):
        self.id = entity_id
        self.issuer = issuer
        self.valid_from = valid_from
        self.credential_subject = credential_subject

        self.valid_until = kwargs.get('valid_until', None)


class AchievementSubject:
    def __init__(self, achievement, identifier=None):
        self.type = ['AchievementSubject']
        self.achievement = achievement
        self.identifier = identifier

    @staticmethod
    def from_badge_instance(badge_instance: BadgeInstance) -> 'AchievementSubject':
        achievement = Achievement.from_badge_instance(badge_instance)
        if badge_instance.recipient_identifier and badge_instance.salt:
            # Hardcoded to one element. The spec allows more, but we don't need it.
            identifier = [IdentityObject.from_badge_instance(badge_instance)]
        else:
            identifier = None

        return AchievementSubject(achievement=achievement, identifier=identifier)


class IdentityObject:
    """
    Represents an identity object for a recipient.
    The name is a bit misleading, as it's not an object in the sense of a Python object,
    but contrary to all other "objects" in the OBv3 spec, it's what the spec calls it.
    """

    def __init__(self, recipient_identifier, salt, hasher=generate_sha256_hashstring):
        self.identity_hash = hasher(recipient_identifier, salt)
        self.identity_type = 'emailAddress'
        self.hashed = True
        self.salt = salt

    @staticmethod
    def from_badge_instance(badge_instance):
        return IdentityObject(badge_instance.recipient_identifier, badge_instance.salt)


class Achievement(StructFieldsMixin):
    FIELDS = [
        'id',
        'criteria',
        'description',
        'ects',
        'education_program_identifier',
        'image',
        'in_language',
        'name',
        'participation',
        'alignment',
    ]

    @staticmethod
    def from_badge_instance(badge_instance: BadgeInstance) -> 'Achievement':
        badge_class = badge_instance.badgeclass
        in_language = None
        ects = None
        education_program_identifier = None

        if 'extensions:LanguageExtension' in badge_class.extension_items:
            in_language = badge_class.extension_items['extensions:LanguageExtension']['Language']

        if 'extensions:ECTSExtension' in badge_class.extension_items:
            ects = badge_class.extension_items['extensions:ECTSExtension']['ECTS']

        if 'extensions:EducationProgramIdentifierExtension' in badge_class.extension_items:
            education_program_identifier = badge_class.extension_items[
                'extensions:EducationProgramIdentifierExtension'
            ]['EducationProgramIdentifier']

        return Achievement(
            id=badge_instance.entity_id,
            criteria={'narrative': badge_class.criteria_text},
            description=badge_class.description,
            name=badge_class.name,
            image={'id': badge_class.image_url()},
            in_language=in_language,
            ects=ects,
            education_program_identifier=education_program_identifier,
            participation=badge_class.participation,
            alignment=badge_class.alignment_items,
        )
