from django.conf import settings
from mainsite.models import BadgrApp
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from badgeuser.models import TermsVersion

# BadgrApp
BadgrApp(
    is_active=1,
    cors="localhost:4000",
    email_confirmation_redirect="http://127.0.0.1:4000/login/",
    forgot_password_redirect="http://127.0.0.1:4000/change-password/",
    name="localhost",
    signup_redirect="http://127.0.0.1:4000/signup/",
    ui_login_redirect="http://127.0.0.1:4000/auth/login/",
    ui_signup_success_redirect="http://127.0.0.1:4000/signup/success/",
    ui_connect_success_redirect="http://127.0.0.1:4000/profile/",
    public_pages_redirect="http://127.0.0.1:4000/public/",
    oauth_authorization_redirect="http://127.0.0.1:4000/oauth/",
    use_auth_code_exchange=0
).save()


# Site
Site(domain="127.0.0.1", name="127.0.0.1").save()
Site(domain="localhost", name="localhost").save()


# SocialApp
edu_id_secret = settings.EDU_ID_SECRET
SocialApp(
    provider="edu_id",
    name="edu_id",
    client_id="edubadges",
    secret=edu_id_secret
).save()


surf_conext_secret = settings.SURF_CONEXT_SECRET
SocialApp(
    provider="surf_conext",
    name="surf_conext",
    client_id="http@//localhost.edubadges.nl",
    secret=surf_conext_secret
).save()

SocialApp.objects.get(name="edu_id").sites.add(Site.objects.get(name="localhost"))
SocialApp.objects.get(name="edu_id").sites.add(Site.objects.get(name="127.0.0.1"))
SocialApp.objects.get(name="surf_conext").sites.add(Site.objects.get(name="localhost"))
SocialApp.objects.get(name="surf_conext").sites.add(Site.objects.get(name="127.0.0.1"))


# TermsVersion
TermsVersion(version=1, is_active=1).save()