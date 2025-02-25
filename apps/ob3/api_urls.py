from django.urls import re_path
from django_api_proxy.views import ProxyView

from ob3.api import CredentialsView

urlpatterns = [
    re_path(r'^v1/ob3', CredentialsView.as_view(), name='credentials'),
    re_path(
        r'^.well-known/oauth-authorization-server',
        ProxyView.as_view(source='.well-known/oauth-authorization-server'),
        name='oauth-authorization-server',
    ),
    re_path(
        r'^.well-known/openid-credential-issuer',
        ProxyView.as_view(source='.well-known/openid-credential-issuer'),
        name='openid-credential-issuer',
    ),
    re_path(r'^auth/token', ProxyView.as_view(source='auth/token'), name='auth-token'),
    re_path(r'^openid4vci/credential', ProxyView.as_view(source='openid4vci/credential'), name='openid4vci-credential'),
]
