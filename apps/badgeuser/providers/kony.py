from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth.provider import OAuthProvider


class KonyAccount(ProviderAccount):
    pass


class KonyProvider(OAuthProvider):
    id = 'kony'
    name = 'Kony'
    package = 'badgeuser.providers.kony'
    account_class = KonyAccount

providers.registry.register(KonyProvider)
