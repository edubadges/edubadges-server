import importlib

from allauth.socialaccount import providers
from django.urls import path, re_path

from badgrsocialauth.views import (
    BadgrSocialLogin,
    BadgrSocialEmailExists,
    BadgrSocialAccountVerifyEmail,
    BadgrSocialLoginCancel,
    BadgrAccountConnected,
    ImpersonateUser,
)

urlpatterns = [
    re_path(r'^sociallogin', BadgrSocialLogin.as_view(permanent=False), name='socialaccount_login'),
    # Intercept allauth cancel login view
    re_path(r'^cancellogin', BadgrSocialLoginCancel.as_view(permanent=False), name='socialaccount_login_cancelled'),
    # Intercept allauth signup view (if account with given email already exists) and redirect to UI
    re_path(r'^emailexists', BadgrSocialEmailExists.as_view(permanent=False), name='socialaccount_signup'),
    # Intercept allauth email verification view and redirect to UI
    re_path(
        r'^verifyemail', BadgrSocialAccountVerifyEmail.as_view(permanent=False), name='account_email_verification_sent'
    ),
    # Intercept allauth connections view (attached a new social account)
    re_path(r'^connected', BadgrAccountConnected.as_view(permanent=False), name='socialaccount_connections'),
    path('impersonate/<str:id>', ImpersonateUser.as_view(), name='impersonate_user'),
]

for provider in providers.registry.get_list():
    try:
        prov_mod = importlib.import_module(provider.get_package() + '.urls')
    except ImportError:
        continue
    prov_urlpatterns = getattr(prov_mod, 'urlpatterns', None)
    if prov_urlpatterns:
        urlpatterns += prov_urlpatterns
