from allauth.account.adapter import DefaultAccountAdapter
from badgeuser.authcode import authcode_for_accesstoken
from badgeuser.models import BadgrAccessToken
from badgrsocialauth.utils import set_url_query_params, get_session_badgr_app
from django.conf import settings
from mainsite.models import EmailBlacklist


class BadgrAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context, attachment=None):
        context['STATIC_URL'] = getattr(settings, 'STATIC_URL')
        context['HTTP_ORIGIN'] = getattr(settings, 'HTTP_ORIGIN')
        context['unsubscribe_url'] = getattr(settings, 'HTTP_ORIGIN') + EmailBlacklist.generate_email_signature(email)

        msg = self.render_mail(template_prefix, email, context)
        if attachment:
            msg.attach(attachment.name, attachment.read())
        msg.send()

    def is_open_for_signup(self, request):
        return getattr(settings, 'OPEN_FOR_SIGNUP', True)


    def get_login_redirect_url(self, request):
        """
        If successfully logged in, redirect to the front-end, including an authToken query parameter.
        """
        if request.user.is_authenticated:
            badgr_app = get_session_badgr_app(request)

            if badgr_app is not None:
                accesstoken = BadgrAccessToken.objects.generate_new_token_for_user(
                    request.user,
                    application=badgr_app.oauth_application if badgr_app.oauth_application_id else None,
                    scope='rw:backpack rw:profile rw:issuer')

                if badgr_app.use_auth_code_exchange:
                    authcode = authcode_for_accesstoken(accesstoken)
                    params = dict(authCode=authcode)
                else:
                    params = dict(authToken=accesstoken.token)

                return set_url_query_params(badgr_app.ui_login_redirect, **params)
        else:
            return '/'