import urllib

from allauth.account.utils import user_email
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount import app_settings
from django.conf import settings
from allauth.utils import email_address_exists
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse
from rest_framework.exceptions import AuthenticationFailed

from badgrsocialauth.utils import set_session_verification_email, get_session_auth_token, get_verified_user, \
    get_session_badgr_app, set_url_query_params


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        badgr_app = get_session_badgr_app(self.request)
        redirect_url = "{url}?authError={message}".format(
            url=badgr_app.ui_login_redirect,
            message=urllib.quote("Authentication error. "+error))
        raise ImmediateHttpResponse(HttpResponseRedirect(redirect_to=redirect_url))

    def _update_session(self, request, sociallogin):
        email = user_email(sociallogin.user)
        set_session_verification_email(request, email)

    def save_user(self, request, sociallogin, form=None):
        """
        Store verification email in session so that it can be retrieved/forwarded when redirecting to front-end.
        """
        self._update_session(request, sociallogin)

        return super(BadgrSocialAccountAdapter, self).save_user(request, sociallogin, form)

    def pre_social_login(self, request, sociallogin):
        """
        Retrieve and verify (again) auth token that was provided with initial connect request.  Store as request.user,
        as required for socialauth connect logic.
        """
        self._update_session(request, sociallogin)
        try:
            auth_token = get_session_auth_token(request)
            if auth_token is not None:
                verified_user = get_verified_user(auth_token)
                request.user = verified_user
                if sociallogin.is_existing and verified_user != sociallogin.user:
                    badgr_app = get_session_badgr_app(self.request)
                    redirect_url = "{url}?authError={message}".format(
                        url=badgr_app.ui_connect_success_redirect,
                        message=urllib.quote("Could not add social login. This account is already associated with a user."))
                    raise ImmediateHttpResponse(HttpResponseRedirect(redirect_to=redirect_url))
        except AuthenticationFailed as e:
            raise ImmediateHttpResponse(HttpResponseForbidden(e.detail))


    def is_auto_signup_allowed(self, request, sociallogin):
        # If email is specified, check for duplicate and if so, no auto signup.
        auto_signup = app_settings.AUTO_SIGNUP
        if auto_signup:
            email = user_email(sociallogin.user)
            # Let's check if auto_signup is really possible...
            if email:
                if settings.ACCOUNT_UNIQUE_EMAIL:
                    # Change: in Badge always check for email
                    if email_address_exists(email):
                        # Oops, another user already has this address.
                        # Otherwise False, because we cannot trust which provider properly verified the emails.
                        auto_signup = False
            elif app_settings.EMAIL_REQUIRED:
                # Nope, email is required and we don't have it yet...
                auto_signup = False
        return auto_signup