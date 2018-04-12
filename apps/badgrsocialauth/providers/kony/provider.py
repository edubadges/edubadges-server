from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth.provider import OAuthProvider


class KonyAccount(ProviderAccount):
    pass


class KonyProvider(OAuthProvider):
    id = 'kony'
    name = 'Kony'
    package = 'badgrsocialauth.providers.kony'
    account_class = KonyAccount

    def extract_uid(self, data):
        return data['user_guid']

    def extract_common_fields(self, data):
        return {
            'email': data['primary_email'],
            'first_name': data['first_name'],
            'last_name': data['last_name']
        }


providers.registry.register(KonyProvider)
