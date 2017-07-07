from allauth.account.utils import user_email
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.http import HttpResponseForbidden
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

from badgrsocialauth.utils import set_session_verification_email, get_session_auth_token, get_verified_user


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        # Dirty hack: store verification email in session so that it can be retrieved/forwarded when redirecting to
        # front-end despite allauth's lack of support for this feature
        email = user_email(sociallogin.user)
        set_session_verification_email(request, email)

        return super(BadgrSocialAccountAdapter, self).save_user(request, sociallogin, form)

    def pre_social_login(self, request, sociallogin):
        """
        Retrieve and verify auth token that was provided with initial connect request.  Store as request.user, as
        required for socialauth connect login.
        """

        try:
            auth_token = get_session_auth_token(request)
            verified_user = get_verified_user(auth_token)
        except AuthenticationFailed as e:
            raise ImmediateHttpResponse(HttpResponseForbidden(e.detail))

        if verified_user is not None:
            request.user = verified_user
