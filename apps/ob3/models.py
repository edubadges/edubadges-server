# Description: This file contains the models for the badge-issuing service.

from hashlib import sha256
from typing import Optional

def generate_sha256_hashstring(identifier: str, salt: Optional[str]=None):
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
    key = '{}{}'.format(identifier.lower(), salt if salt is not None else "")
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
            raise ValueError(f"Invalid fields provided: {invalid_fields}")

        # Check for missing fields
        missing_fields = set(self.FIELDS) - set(kwargs.keys())
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")

        for field in self.FIELDS:
            setattr(self, field, kwargs.get(field, None))
        for key, value in kwargs.items():
            setattr(self, key, value)

# A plain old Python object (POPO) that represents an educational credential
class OfferRequest:
    def __init__(self, offer_id, credential_configuration_id, badge_instance):
        self.offer_id = offer_id
        self.credential_configuration_id = credential_configuration_id

        credential_subject = AchievementSubject.from_badge_instance(badge_instance)
        self.credential = Credential(
            issuer=badge_instance.badgeclass.issuer,
            valid_from = badge_instance.issued_on,
            credential_subject=credential_subject,
        )

        if badge_instance.expires_at:
            self.credential.valid_until = badge_instance.expires_at

class Credential:
    def __init__(self, issuer, valid_from, credential_subject, **kwargs):
        self.issuer = issuer
        self.valid_from = valid_from
        self.credential_subject = credential_subject

        self.valid_until = kwargs.get('valid_until', None)

class AchievementSubject:
    def __init__(self, achievement, identifier=None):
        self.type = ["AchievementSubject"]
        self.achievement = achievement
        self.identifier = identifier

    @staticmethod
    def from_badge_instance(badge_instance):
        achievement = Achievement.from_badge_instance(badge_instance)
        if badge_instance.recipient_identifier and badge_instance.salt:
            # Hardcoded to one element. The spec allows more, but we don't need it.
            identifier = [IdentityObject.from_badge_instance(badge_instance)]
        else:
            identifier = None

        return AchievementSubject(
                achievement=achievement,
                identifier=identifier
        )

class IdentityObject:
    """
    Represents an identity object for a recipient.
    The name is a bit misleading, as it's not an object in the sense of a Python object,
    but contrary to all other "objects" in the OBv3 spec, it's what the spec calls it.
    """
    def __init__(self, recipient_identifier, salt, hasher=generate_sha256_hashstring):
        self.identity_hash = hasher(
                recipient_identifier,
                salt
        )
        self.identity_type = "emailAddress"
        self.hashed = True
        self.salt = salt

    @staticmethod
    def from_badge_instance(badge_instance):
        return IdentityObject(
                badge_instance.recipient_identifier,
                badge_instance.salt
        )

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
    def from_badge_instance(badge_instance):
        badge_class = badge_instance.badgeclass
        in_language = None
        ects = None
        education_program_identifier = None

        if "extensions:LanguageExtension" in badge_class.extension_items:
            in_language = badge_class.extension_items["extensions:LanguageExtension"]["Language"]

        if "extensions:ECTSExtension" in badge_class.extension_items:
            ects = badge_class.extension_items["extensions:ECTSExtension"]["ECTS"]

        if "extensions:EducationProgramIdentifierExtension" in badge_class.extension_items:
            education_program_identifier = badge_class.extension_items["extensions:EducationProgramIdentifierExtension"]["EducationProgramIdentifier"]

        return Achievement(
            id=badge_instance.entity_id,
            criteria= { "narrative": badge_class.criteria_text },
            description=badge_class.description,
            name=badge_class.name,
            image= { "id": badge_class.image_url() },
            in_language=in_language,
            ects=ects,
            education_program_identifier=education_program_identifier,
            participation=badge_class.participation,
            alignment=badge_class.alignment_items
        )

