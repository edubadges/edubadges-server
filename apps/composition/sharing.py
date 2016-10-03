import urllib

from django.conf import settings


class ShareProvider(object):
    provider_code = None

    def __init__(self, provider):
        self.provider = provider


class FacebookShareProvider(ShareProvider):
    provider_code = 'facebook'
    provider_name = 'Facebook'

    def share_url(self, badge_instance):
        return "https://www.facebook.com/sharer/sharer.php?u={url}".format(
            url=urllib.quote(badge_instance.share_url)
        )


class LinkedinShareProvider(ShareProvider):
    provider_code = 'linkedin'
    provider_name = 'LinkedIn'

    def share_url(self, instance, **kwargs):
        url = self.certification_share_url(instance, **kwargs)
        if not url:
            url = self.feed_share_url(instance, **kwargs)
        return url

    def feed_share_url(self, badge_instance, title=None, summary=None):
        if title is None:
            title = "I earned a badge from Badgr!"
        if summary is None:
            summary = badge_instance.cached_badgeclass.name,
        return "https://www.linkedin.com/shareArticle?mini=true&url={url}&title={title}&summary={summary}".format(
            url=urllib.quote(badge_instance.share_url),
            title=title,
            summary=summary
        )

    def certification_share_url(self, badge_instance, **kwargs):
        cert_issuer_id = getattr(settings, 'LINKEDIN_CERTIFICATION_ISSUER_ID', None)
        if cert_issuer_id is None:
            return None
        return "https://www.linkedin.com/profile/add?_ed={certIssuerId}&pfCertificationName={name}&pfCertificationUrl={url}".format(
            certIssuerId=cert_issuer_id,
            name=urllib.quote(badge_instance.cached_badgeclass.name),
            url=urllib.quote(badge_instance.share_url)
        )


class SharingManager(object):
    provider_code = None
    ManagerProviders = {
        FacebookShareProvider.provider_code: FacebookShareProvider,
        LinkedinShareProvider.provider_code: LinkedinShareProvider,
    }

    @classmethod
    def share_url(cls, provider, badge_instance, **kwargs):
        manager_cls = SharingManager.ManagerProviders.get(provider.lower(), None)
        if manager_cls is None:
            raise NotImplementedError(u"Provider not supported: {}".format(provider))
        manager = manager_cls(provider)
        url = manager.share_url(badge_instance, **kwargs)
        return url
