from allauth.account.utils import user_email
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseForbidden
from rest_framework.exceptions import AuthenticationFailed

from badgrsocialauth.utils import set_session_verification_email, get_session_auth_token, get_verified_user


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):

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
        except AuthenticationFailed as e:
            raise ImmediateHttpResponse(HttpResponseForbidden(e.detail))

