import urllib, unicodedata
import urlparse

from rest_framework.authentication import TokenAuthentication

from mainsite.models import BadgrApp

from allauth.account.models import EmailAddress
from allauth.socialaccount.providers.base import ProviderAccount


class BadgrSocialAuthProviderMixin:
    """
    Overrides common patterns that assist in callback function
    """
 
    account_class = ProviderAccount
 
    def extract_uid(self, response):
        return response['sub']
 
    def extract_extra_data(self, response):
        return response
 
    def extract_email_addresses(self, data, user=None):
        # Force verification of email addresses because SurfConext will only transmit verified emails
        if data.get('email'):
            return [EmailAddress(email=data['email'].strip().lower(),
                                 verified=True,
                                 primary=True)]
        else:
            return []
 
    def extract_common_fields(self, data):
        # extracts data required to build user model
        return dict( # email=data['email'],
                    email = data.get('email', None),
                    first_name=data.get('given_name', None),
                    last_name=data.get('family_name', None)
                    )

def get_social_account(sociallogin_identifier):
    from allauth.socialaccount.models import SocialAccount
    try:
        social_account = SocialAccount.objects.get(uid=sociallogin_identifier)
        return social_account
    except SocialAccount.DoesNotExist:
        return None

def set_url_query_params(url, **kwargs):
    """
    Given a url, possibly including query parameters, return a url with the given query parameters set, replaced on a
    per-key basis.
    """
    url_parts = list(urlparse.urlparse(url))
    query = dict(urlparse.parse_qsl(url_parts[4]))
    query.update(kwargs)
    url_parts[4] = urllib.urlencode(query)
    return urlparse.urlunparse(url_parts)


def get_session_verification_email(request):
    return request.session.get('verification_email', None)


def set_session_verification_email(request, verification_email):
    request.session['verification_email'] = verification_email


def get_session_badgr_app(request):
    try:
        if request and hasattr(request, 'session'):
            return BadgrApp.objects.get(pk=request.session.get('badgr_app_pk', None))
    except BadgrApp.DoesNotExist:
        return None


def set_session_badgr_app(request, badgr_app):
    request.session['badgr_app_pk'] = badgr_app.pk


def get_session_authcode(request):
    return request.session.get('badgr_authcode', None)


def set_session_authcode(request, authcode):
    request.session['badgr_authcode'] = authcode


def get_verified_user(auth_token):
    authenticator = TokenAuthentication()
    verified_user, _ = authenticator.authenticate_credentials(auth_token)
    return verified_user

def update_user_params(user, userinfo):
    if userinfo.get('given_name'):
        user.first_name = userinfo['given_name']
        user.save()
    if userinfo.get('family_name'):
        user.last_name = userinfo['family_name']
        user.save()
    if userinfo.get('email'):
        user_emails = user.email_items
        email_found = False
        for email in user_emails:
            email_and_variants = [email] + list(email.cached_variants())
            if userinfo['email'] in [email_variant.email for email_variant in email_and_variants]: # the email is already there, make it verified
                email.verified = True
                email.save()
                email_found = True
                break
        if not email_found: # no email, make a new verified one
            new_email = EmailAddress.objects.create(email=userinfo['email'],
                                                    verified = True,
                                                    primary = False,
                                                    user = user)

