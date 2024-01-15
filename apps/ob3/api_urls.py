from django.conf.urls import url
from django_api_proxy.views import ProxyView

from ob3.api import CredentialsView

urlpatterns = [
    url(r'^v1/ob3', CredentialsView.as_view(), name='credentials'),
    url(r'^.well-known/oauth-authorization-server',
        ProxyView.as_view(source='.well-known/oauth-authorization-server'), name='oauth-authorization-server'),
    url(r'^.well-known/openid-credential-issuer',
        ProxyView.as_view(source='.well-known/openid-credential-issuer'), name='openid-credential-issuer'),
    url(r'^auth/token', ProxyView.as_view(source='auth/token'), name='auth-token'),
    url(r'^openid4vci/credential', ProxyView.as_view(source='openid4vci/credential'),
        name='openid4vci-credential'),

]
