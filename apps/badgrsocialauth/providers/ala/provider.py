from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class AlaProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'ala'
    name = 'Ala'
    package = 'badgrsocialauth.providers.ala'

providers.registry.register(AlaProvider)
