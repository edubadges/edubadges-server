from allauth.account.utils import user_email
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from badgrsocialauth.utils import set_session_verification_email


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        # Dirty hack: store verification email in session so that it can be retrieved/forwarded when redirecting to
        # front-end despite allauth's lack of support for this feature
        email = user_email(sociallogin.user)
        set_session_verification_email(request, email)

        return super(BadgrSocialAccountAdapter, self).save_user(request, sociallogin, form)
