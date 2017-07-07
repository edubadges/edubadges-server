import logging
import urllib
import urlparse

from allauth.account.utils import user_pk_to_url_str
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.tokens import default_token_generator
from django.core.urlresolvers import resolve, Resolver404, reverse

from allauth.account.adapter import DefaultAccountAdapter, get_adapter
from allauth.account import app_settings
from allauth.account.models import EmailConfirmation
from allauth.utils import get_current_site, build_absolute_uri

from badgeuser.models import CachedEmailAddress
from badgrsocialauth.utils import set_url_query_params, get_session_badgr_app, set_session_badgr_app
from mainsite.models import BadgrApp, EmailBlacklist
from mainsite.utils import OriginSetting


class BadgrAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        context['STATIC_URL'] = getattr(settings, 'STATIC_URL')
        context['HTTP_ORIGIN'] = getattr(settings, 'HTTP_ORIGIN')
        context['unsubscribe_url'] = getattr(settings, 'HTTP_ORIGIN') + EmailBlacklist.generate_email_signature(email)

        msg = self.render_mail(template_prefix, email, context)
        msg.send()

    def is_open_for_signup(self, request):
        return getattr(settings, 'OPEN_FOR_SIGNUP', True)

    def get_email_confirmation_redirect_url(self, request):
        """
        The URL to return to after successful e-mail confirmation.
        """
        badgr_app = BadgrApp.objects.get_current(request)
        if not badgr_app:
            logger = logging.getLogger(self.__class__.__name__)
            logger.warning("Could not determine authorized badgr app")
            return super(BadgrAccountAdapter, self).get_email_confirmation_redirect_url(request)

        try:
            resolverMatch = resolve(request.path)
            confirmation = EmailConfirmation.objects.get(pk=resolverMatch.kwargs.get('confirm_id'))
            # publish changes to cache
            email_address = CachedEmailAddress.objects.get(pk=confirmation.email_address_id)
            email_address.save()

            redirect_url = urlparse.urljoin(
                badgr_app.email_confirmation_redirect.rstrip('/') + '/',
                urllib.quote(email_address.user.first_name.encode('utf8'))
            )
            redirect_url = set_url_query_params(redirect_url, email=email_address.email.encode('utf8'))

            return redirect_url

        except Resolver404, EmailConfirmation.DoesNotExist:
            return badgr_app.email_confirmation_redirect

    def get_email_confirmation_url(self, request, emailconfirmation):
        url_name = "v1_api_user_email_confirm"
        temp_key = default_token_generator.make_token(emailconfirmation.email_address.user)
        token = "{uidb36}-{key}".format(uidb36=user_pk_to_url_str(emailconfirmation.email_address.user),
                                        key=temp_key)
        activate_url = OriginSetting.HTTP + reverse(url_name, kwargs={'confirm_id': emailconfirmation.pk})
        tokenized_activate_url = "{}?token={}".format(activate_url, token)
        return tokenized_activate_url

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        current_site = get_current_site(request)
        activate_url = self.get_email_confirmation_url(
            request,
            emailconfirmation)
        ctx = {
            "user": emailconfirmation.email_address.user,
            "email": emailconfirmation.email_address,
            "activate_url": activate_url,
            "current_site": current_site,
            "key": emailconfirmation.key,
        }
        if signup == 'canvas':
            email_template = 'account/email/email_confirmation_canvas'
        elif signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'
        get_adapter().send_mail(email_template,
                                emailconfirmation.email_address.email,
                                ctx)

    def get_login_redirect_url(self, request):
        """
        If successfully logged in, redirect to the front-end, including an authToken query parameter.
        """
        if request.user.is_authenticated():
            badgr_app = get_session_badgr_app(request)

            if badgr_app is not None:
                return set_url_query_params(badgr_app.ui_login_redirect,
                                            authToken=request.user.auth_token)
        else:
            return '/'

    def login(self, request, user):
        """
        Preserve badgr_app session data across Django login() boundary
        """
        badgr_app = get_session_badgr_app(request)
        ret = super(BadgrAccountAdapter, self).login(request, user)
        set_session_badgr_app(request, badgr_app)
        return ret
