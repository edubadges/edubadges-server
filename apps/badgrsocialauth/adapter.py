import urllib

from allauth.account.utils import user_email
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseForbidden, HttpResponseRedirect
from rest_framework.exceptions import AuthenticationFailed

from badgeuser.authcode import accesstoken_for_authcode
from badgrsocialauth.utils import set_session_verification_email, get_session_badgr_app, get_session_authcode


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        badgr_app = get_session_badgr_app(self.request)
        redirect_url = "{url}?authError={message}".format(
            url=badgr_app.ui_login_redirect,
            message=urllib.quote("Authentication error"))
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
            authcode = get_session_authcode(request)
            if authcode is not None:
                accesstoken = accesstoken_for_authcode(authcode)
                if not accesstoken:
                    raise ImmediateHttpResponse(HttpResponseForbidden())

                request.user = accesstoken.user
                if sociallogin.is_existing and accesstoken.user != sociallogin.user:
                    badgr_app = get_session_badgr_app(self.request)
                    redirect_url = "{url}?authError={message}".format(
                        url=badgr_app.ui_connect_success_redirect,
                        message=urllib.quote("Could not add social login. This account is already associated with a user."))
                    raise ImmediateHttpResponse(HttpResponseRedirect(redirect_to=redirect_url))
        except AuthenticationFailed as e:
            raise ImmediateHttpResponse(HttpResponseForbidden(e.detail))

