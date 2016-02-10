import logging

from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import resolve, Resolver404

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account import app_settings
from allauth.account.models import EmailConfirmation

from mainsite.models import BadgrApp


class BadgrAccountAdapter(DefaultAccountAdapter):

    def send_mail(self, template_prefix, email, context):
        context['STATIC_URL'] = getattr(settings, 'STATIC_URL')
        context['HTTP_ORIGIN'] = getattr(settings, 'HTTP_ORIGIN')

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
            user = EmailConfirmation.objects.get(key=resolverMatch.kwargs.get('key')).email_address.user
            return badgr_app.email_confirmation_redirect + user.first_name
        except Resolver404, EmailConfirmation.DoesNotExist:
            return badgr_app.email_confirmation_redirect
