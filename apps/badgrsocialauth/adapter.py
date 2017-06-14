from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        This is a hack, required to preserve the information about the final_redirect_url
        across the login/logout calls which are performed by allauth when processing
        a callback request and destroy the current session information.

        It is not sufficient to override BadgrAccountAdapter.login() to preserve this
        information because logout() called first if there is already a logged-in user,
        and there is no corresponding logout hook in DefaultAccountAdapter.

        Thus, the front-end redirect would not occur for users who are already authenticated
        to badgr-server, either from a previous login or use of the admin panel.
        """
        final_redirect_url = request.session.get('final_redirect_url', None)
        request.final_redirect_url = final_redirect_url