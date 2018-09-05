from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider
from badgrsocialauth.utils import BadgrSocialAuthProviderMixin

class EduIDProvider(BadgrSocialAuthProviderMixin, Provider):
    id = 'edu_id'
    name = 'EduId'
    package = 'badgrsocialauth.providers.eduid'

providers.registry.register(EduIDProvider)
