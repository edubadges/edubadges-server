# A plain old Python object (POPO) that represents an educational credential

class EduCredential:
    def __init__(self, offer_id, credential_configuration_id, badge_instance):
        self.offer_id = offer_id
        self.credential_configuration_id = credential_configuration_id
        self.credential = Credential(
            issuer=badge_instance.badgeclass.issuer,
            valid_from = badge_instance.issued_on,
            credential_subject= { "achievement": Achievement.from_badge_instance(badge_instance) }
        )

        if badge_instance.expires_at:
            self.credential.valid_until = badge_instance.expires_at

class Credential:
    def __init__(self, issuer, valid_from, credential_subject, **kwargs):
        self.issuer = issuer
        self.valid_from = valid_from
        self.credential_subject = credential_subject

        self.valid_until = kwargs.get('valid_until', None)

class Achievement:
    def __init__(self, id, criteria, description, name, image, in_language):
        self.id = id
        self.criteria = criteria
        self.description = description
        self.name = name
        self.image = image
        self.in_language = in_language

    @staticmethod
    def from_badge_instance(badge_instance):
        badge_class = badge_instance.badgeclass
        in_language = None
        if "extensions:LanguageExtension" in badge_class.extension_items:
            in_language = badge_class.extension_items["extensions:LanguageExtension"]["Language"]

        return Achievement(
            id=badge_instance.entity_id,
            criteria= { "narrative": badge_class.criteria_text }, 
            description=badge_class.description,
            name=badge_class.name,
            image= { "id": badge_class.image_url() },
            in_language=in_language
        )
