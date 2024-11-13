# A plain old Python object (POPO) that represents an educational credential
class EduCredential:
    def __init__(self, offer_id, credential_configuration_id, badge_instance):
        self.offer_id = offer_id
        self.credential_configuration_id = credential_configuration_id
        self.credential = Credential(
            issuer=badge_instance.badgeclass.issuer,
            credential_subject= { "achievement": Achievement.from_badge_instance(badge_instance) }
        )

class Credential:
    def __init__(self, issuer, credential_subject):
        self.issuer = issuer
        self.credential_subject = credential_subject

class Achievement:
    def __init__(self, id, criteria, description, name, image):
        self.id = id
        self.criteria = criteria
        self.description = description
        self.name = name
        self.image = image

    @staticmethod
    def from_badge_instance(badge_instance):
        badge_class = badge_instance.badgeclass
        return Achievement(
            id=badge_instance.entity_id,
            criteria= { "narrative": badge_class.criteria_text }, 
            description=badge_class.description,
            name=badge_class.name,
            image= { "id": badge_class.image_url() }
        )
