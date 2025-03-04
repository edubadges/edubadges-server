from .base import BaseBadgrEvent


class BaseBadgeAssertionEvent(BaseBadgrEvent):
    def __init__(self, badge_instance, request):
        self.badge_instance = badge_instance
        self.request = request

    def to_representation(self):
        return {'badgeInstance': self.badge_instance.json, 'referer': self.request.headers.get('referer')}


class BadgeAssertionCheckedEvent(BaseBadgeAssertionEvent):
    pass


class RevokedBadgeAssertionCheckedEvent(BaseBadgeAssertionEvent):
    pass


class BadgeInstanceDownloadedEvent(BaseBadgeAssertionEvent):
    pass


class BadgeClassRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class BadgeClassCriteriaRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class BadgeClassImageRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class IssuerRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class IssuerPublicKeyRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class IssuerBadgesRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class IssuerImageRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class InstitutionImageRetrievedEvent(BaseBadgeAssertionEvent):
    pass


class FacultyImageRetrievedEvent(BaseBadgeAssertionEvent):
    pass
