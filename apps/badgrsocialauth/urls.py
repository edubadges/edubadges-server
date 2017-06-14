from allauth.socialaccount import providers
from django.conf.urls import url
from django.utils import importlib

from badgrsocialauth.views import BadgrSocialLogin, BadgrSocialEmailExists, BadgrSocialAccountVerifyEmail

urlpatterns = [
    url(r'^sociallogin', BadgrSocialLogin.as_view(permanent=False)),

    # Intercept allauth connect view (if account with given email already exists) and redirect to UI
    url(r'^emailexists', BadgrSocialEmailExists.as_view(permanent=False), name='socialaccount_signup'),

    # Intercept allauth email verification view and redirect to UI
    url(r'^verifyemail', BadgrSocialAccountVerifyEmail.as_view(permanent=False), name='account_email_verification_sent'),
]


for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.package + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns