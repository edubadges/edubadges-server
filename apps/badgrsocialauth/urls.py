from allauth.socialaccount import providers
from django.conf.urls import url
from django.utils import importlib

from badgrsocialauth.views import BadgrSocialLogin

urlpatterns = [
    url(r'^do_auth_flow', BadgrSocialLogin.as_view(permanent=False))
]

for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns