from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class SurfconextAlaProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'surfconext_ala'
    name = 'Surfconext_ala'
    package = 'badgrsocialauth.providers.surfconext_ala'

providers.registry.register(SurfconextAlaProvider)
