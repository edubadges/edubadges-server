import json

from allauth.socialaccount import app_settings
from allauth.socialaccount.providers.oauth.client import OAuth
from allauth.socialaccount.providers.oauth.views import (OAuthAdapter,
                                                         OAuthLoginView,
                                                         OAuthCallbackView)

from .provider import KonyProvider


class KonyAPI(OAuth):
    if app_settings.PROVIDERS['kony'].get('environment', 'dev') == 'dev':
        url = 'https://api.dev-kony.com/api/v1_0/whoami'
    elif app_settings.PROVIDERS['kony'].get('environment', 'prod') == 'prod':
        url = 'https://api.kony.com/api/v1_0/whoami'

    def get_user_info(self):
        raw_json = self.query(self.url, method="POST")
        user_info = json.loads(raw_json)
        return user_info


class KonyOAuthAdapter(OAuthAdapter):
    provider_id = KonyProvider.id

    if app_settings.PROVIDERS['kony'].get('environment', 'dev') == 'dev':
        request_token_url = 'https://manage.dev-kony.com/oauth/request_token'
        access_token_url = 'https://manage.dev-kony.com/oauth/access_token'
        authorize_url = 'https://manage.dev-kony.com/oauth/authorize'
    elif app_settings.PROVIDERS['kony'].get('environment', 'dev') == 'prod':
        request_token_url = 'https://manage.kony.com/oauth/request_token'
        access_token_url = 'https://manage.kony.com/oauth/access_token'
        authorize_url = 'https://manage.kony.com/oauth/authorize'

    def complete_login(self, request, app, token, response):
        client = KonyAPI(request, app.client_id, app.secret,
                         self.request_token_url)
        extra_data = client.get_user_info()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)

oauth_login = OAuthLoginView.adapter_view(KonyOAuthAdapter)
oauth_callback = OAuthCallbackView.adapter_view(KonyOAuthAdapter)
