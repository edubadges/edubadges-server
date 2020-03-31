from django.conf import settings
from mainsite.models import BadgrApp
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from badgeuser.models import TermsVersion, BadgeUser

# BadgrApp
BadgrApp.objects.get_or_create(
    is_active=1,
    cors=settings.UI_URL,
    email_confirmation_redirect="{}/login/".format(settings.UI_URL),
    forgot_password_redirect="{}/change-password/".format(settings.UI_URL),
    signup_redirect="{}/signup/".format(settings.UI_URL),
    ui_login_redirect="{}/auth/login/".format(settings.UI_URL),
    ui_signup_success_redirect="{}/signup/success/".format(settings.UI_URL),
    ui_connect_success_redirect="{}/profile/".format(settings.UI_URL),
    public_pages_redirect="{}/public/".format(settings.UI_URL),
    oauth_authorization_redirect="{}/oauth/".format(settings.UI_URL),
    use_auth_code_exchange=0
)

# Site
site, _ = Site.objects.get_or_create(domain=settings.DOMAIN, name=settings.DOMAIN)

# SocialApp
edu_id_secret = settings.EDU_ID_SECRET
edu_id_app, _ = SocialApp.objects.get_or_create(
    provider="edu_id",
    name="edu_id",
    client_id=settings.EDU_ID_CLIENT,
    secret=edu_id_secret
)

surf_conext_secret = settings.SURF_CONEXT_SECRET
surf_conext_app, _ = SocialApp.objects.get_or_create(
    provider="surf_conext",
    name="surf_conext",
    client_id=settings.SURF_CONEXT_CLIENT,
    secret=surf_conext_secret
)

edu_id_app.sites.add(site)
surf_conext_app.sites.add(site)

# TermsVersion
TermsVersion.objects.get_or_create(version=1, is_active=1)

# Superuser
superuser, _ = BadgeUser.objects.get_or_create(
    is_superuser=1,
    username=settings.SUPERUSER_NAME,
    email=settings.SUPERUSER_EMAIL,
    is_staff=1
)
superuser.set_password(settings.SUPERUSER_PWD)
superuser.save()