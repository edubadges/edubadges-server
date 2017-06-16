from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth.provider import OAuthProvider
from allauth.socialaccount import app_settings


class KonyAccount(ProviderAccount):
    pass


class KonyProvider(OAuthProvider):
    id = 'kony'
    name = 'Kony'
    package = 'badgrsocialauth.providers.kony'
    account_class = KonyAccount

    def get_default_scope(self):
        scope = []
        if app_settings.QUERY_EMAIL:
            scope.append('r_emailaddress')
        return scope

    def get_profile_fields(self):
        default_fields = ['id',
                          'first-name',
                          'last-name',
                          'email-address',
                          'picture-url',
                          'picture-urls::(original)', # picture-urls::(original) is higher res
                          'public-profile-url']
        fields = self.get_settings().get('PROFILE_FIELDS',
                                         default_fields)
        return fields

    def extract_uid(self, data):
        return data['id']

    def extract_common_fields(self, data):
        return dict(email=data.get('email-address'),
                    first_name=data.get('first-name'),
                    last_name=data.get('last-name'))


providers.registry.register(KonyProvider)
