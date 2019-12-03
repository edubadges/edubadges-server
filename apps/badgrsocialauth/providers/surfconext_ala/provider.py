from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class SurfconextAlaProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'surfconext_ala'
    name = 'surfconext_ala'
    package = 'badgrsocialauth.providers.surfconext_ala'

    def extract_uid(self, response):
        return "urn:mace:eduid.nl:1.0:{}".format(response['eduid'])

providers.registry.register(SurfconextAlaProvider)
