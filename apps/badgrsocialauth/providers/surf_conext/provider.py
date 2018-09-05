try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from allauth.account.models import EmailAddress
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider, ProviderAccount
from badgeuser.models import BadgeUser
from badgrsocialauth.adapter import BadgrSocialAccountAdapter
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class SurfConextProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'surf_conext'
    name = 'SURFconext'
    package = 'badgrsocialauth.providers.surf_conext'

providers.registry.register(SurfConextProvider)
