from django.conf import settings
from mainsite.models import BadgrApp
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from badgeuser.models import TermsVersion, BadgeUser

# BadgrApp
BadgrApp.objects.get_or_create(
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
)

# Site
site, _ = Site.objects.get_or_create(domain="127.0.0.1", name="127.0.0.1")

# SocialApp
edu_id_secret = settings.EDU_ID_SECRET
edu_id_app, _ = SocialApp.objects.get_or_create(
    provider="edu_id",
    name="edu_id",
    client_id="edubadges",
    secret=edu_id_secret
)

surf_conext_secret = settings.SURF_CONEXT_SECRET
surf_conext_app, _ = SocialApp.objects.get_or_create(
    provider="surf_conext",
    name="surf_conext",
    client_id="http@//localhost.edubadges.nl",
    secret=surf_conext_secret
)

edu_id_app.sites.add(site)
surf_conext_app.sites.add(site)

# TermsVersion
TermsVersion.objects.get_or_create(version=1, is_active=1)

# Superuser
superuser, _ = BadgeUser.objects.get_or_create(
    is_superuser=1,
    username="superuser",
    email="superuser@example.com",
    is_staff=1
)
superuser.set_password("secret")
superuser.save()