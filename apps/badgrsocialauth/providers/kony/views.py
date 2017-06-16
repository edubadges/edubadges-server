from xml.etree import ElementTree
from xml.parsers.expat import ExpatError

from django.utils import six

from allauth.socialaccount import providers
from allauth.socialaccount.providers.oauth.client import OAuth, OAuthClient
from allauth.socialaccount.providers.oauth.views import (OAuthAdapter,
                                                         OAuthLoginView,
                                                         OAuthCallbackView)

from .provider import KonyProvider


class KonyAPI(OAuth):
    url = ' https://api.qa-kony.com/api/v1_0/whoami'

    def get_user_info(self):
        raw_xml = self.query(self.url)


    def to_dict(self, xml):
        """
        Convert XML structure to dict recursively, repeated keys
        entries are returned as in list containers.
        """
        children = list(xml)
        if not children:
            return xml.text
        else:
            out = {}
            for node in list(xml):
                if node.tag in out:
                    if not isinstance(out[node.tag], list):
                        out[node.tag] = [out[node.tag]]
                    out[node.tag].append(self.to_dict(node))
                else:
                    out[node.tag] = self.to_dict(node)
            return out


class KonyOAuthAdapter(OAuthAdapter):
    provider_id = KonyProvider.id
    request_token_url = 'https://manage.dev-kony.com/oauth/request_token'
    access_token_url = 'https://manage.dev-kony.com/oauth/access_token'
    authorize_url = 'https://manage.dev-kony.com/oauth/authorize'

    def complete_login(self, request, app, token, response):
        client = KonyAPI(request, app.client_id, app.secret,
                         self.request_token_url)
        extra_data = client.get_user_info()
        return self.get_provider().sociallogin_from_response(request,
                                                             extra_data)

class KonyOAuthClient(OAuthClient):
    def __init__(self, *args, **kwargs):
        super(KonyOAuthClient, self).__init__(*args, **kwargs)

    def get_redirect(self, authorization_url, extra_params):
        pass


class KonyOAuthLoginView(OAuthLoginView):
    def _get_client(self, request, callback_url):
        provider = self.adapter.get_provider()
        app = provider.get_app(request)
        scope = ' '.join(provider.get_scope(request))
        parameters = {}
        if scope:
            parameters['scope'] = scope
        client = KonyOAuthClient(request, app.client_id, app.secret,
                                 self.adapter.request_token_url,
                                 self.adapter.access_token_url,
                                 callback_url,
                                 parameters=parameters, provider=provider)
        return client


oauth_login = OAuthLoginView.adapter_view(KonyOAuthAdapter)
oauth_callback = OAuthCallbackView.adapter_view(KonyOAuthAdapter)