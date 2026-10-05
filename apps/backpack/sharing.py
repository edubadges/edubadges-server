import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from issuer.models import BadgeInstance


class ShareProvider:
    provider_code = None

    def __init__(self, provider):
        self.provider = provider


class TwitterShareProvider(ShareProvider):
    provider_code = "twitter"
    provider_name = "Twitter"

    def share_url(self, obj, **kwargs):
        if isinstance(obj, BadgeInstance):
            text = f"I earned a badge from {obj.cached_issuer.name}! {obj.share_url}"
        else:
            text = obj.share_url
        return f"https://twitter.com/intent/tweet?text={urllib.parse.quote(text)}"


class FacebookShareProvider(ShareProvider):
    provider_code = "facebook"
    provider_name = "Facebook"

    def share_url(self, badge_instance, **kwargs):
        return f"https://www.facebook.com/sharer/sharer.php?u={urllib.parse.quote(badge_instance.share_url)}"


class PinterestShareProvider(ShareProvider):
    provider_code = "pinterest"
    provider_name = "Pinterest"

    def share_url(self, badge_instance, **kwargs):
        return f"http://www.pinterest.com/pin/create/button/?url={urllib.parse.quote(badge_instance.share_url)}&media={badge_instance.image_url}&description={badge_instance.cached_badgeclass.name}"


class LinkedinShareProvider(ShareProvider):
    provider_code = "linkedin"
    provider_name = "LinkedIn"

    def share_url(self, instance, **kwargs):
        url = None
        # sharing as a certification is broken so disabling for now
        # if hasattr(instance, 'cached_badgeclass'):
        #     url = self.certification_share_url(instance, **kwargs)

        if not url:
            url = self.feed_share_url(instance, **kwargs)
        return url

    def feed_share_url(self, badge_instance, title=None, summary=None):
        if title is None:
            title = "I earned a badge from Badgr!"
        if summary is None:
            summary = (badge_instance.cached_badgeclass.name,)
        return f"https://www.linkedin.com/shareArticle?mini=true&url={urllib.parse.quote(badge_instance.share_url)}&title={title}&summary={summary}"

    def certification_share_url(self, badge_instance, **kwargs):
        cert_issuer_id = getattr(settings, "LINKEDIN_CERTIFICATION_ISSUER_ID", None)
        if cert_issuer_id is None:
            return None
        return f"https://www.linkedin.com/profile/add?_ed={cert_issuer_id}&pfCertificationName={urllib.parse.quote(badge_instance.cached_badgeclass.name)}&pfCertificationUrl={urllib.parse.quote(badge_instance.share_url)}"


class SharingManager:
    provider_code = None
    ManagerProviders = {
        FacebookShareProvider.provider_code: FacebookShareProvider,
        LinkedinShareProvider.provider_code: LinkedinShareProvider,
        TwitterShareProvider.provider_code: TwitterShareProvider,
        PinterestShareProvider.provider_code: PinterestShareProvider,
    }

    @classmethod
    def share_url(cls, provider, badge_instance, **kwargs):
        manager_cls = SharingManager.ManagerProviders.get(provider.lower(), None)
        if manager_cls is None:
            raise NotImplementedError(f"Provider not supported: {provider}")
        manager = manager_cls(provider)
        url = manager.share_url(badge_instance, **kwargs)
        return url

    @classmethod
    def is_provider_supported(cls, provider):
        return provider in SharingManager.ManagerProviders
