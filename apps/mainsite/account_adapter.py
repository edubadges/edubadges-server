from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import resolve, Resolver404

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account import app_settings
from allauth.account.models import EmailConfirmation


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
        try:
            resolverMatch = resolve(request.path)
            user = EmailConfirmation.objects.get(key=resolverMatch.kwargs.get('key')).email_address.user
            return app_settings.EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL + user.first_name
        except Resolver404, EmailConfirmation.DoesNotExist:
            return app_settings.EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL
