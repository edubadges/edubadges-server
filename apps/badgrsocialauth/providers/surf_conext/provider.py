from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class SurfConextProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'surf_conext'
    name = 'SURFconext'
    package = 'badgrsocialauth.providers.surf_conext'

providers.registry.register(SurfConextProvider)
