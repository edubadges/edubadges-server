import logging
import urlparse

from django.conf import settings
from django.contrib.auth import logout
from django.core.urlresolvers import resolve, Resolver404, reverse

from allauth.account.adapter import DefaultAccountAdapter, get_adapter
from allauth.account import app_settings
from allauth.account.models import EmailConfirmation
from allauth.utils import get_current_site, build_absolute_uri

from badgeuser.models import CachedEmailAddress
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
            confirmation = EmailConfirmation.objects.get(key=resolverMatch.kwargs.get('key'))
            # publish changes to cache
            email_address = CachedEmailAddress.objects.get(pk=confirmation.email_address_id)
            email_address.save()

            if resolverMatch.url_name == 'legacy_confirm_email':
                return reverse('account_login')

            return "{}{}?email={}".format(
                badgr_app.email_confirmation_redirect,
                email_address.user.first_name,
                email_address.email
            )

        except Resolver404, EmailConfirmation.DoesNotExist:
            return badgr_app.email_confirmation_redirect

    def get_email_confirmation_url(self, request, emailconfirmation):
        if request is not None:
            referer = request.META.get('HTTP_REFERER')
            parsed = urlparse.urlparse(referer)
            try:
                badgr_app = BadgrApp.cached.get(cors=parsed.netloc)
            except BadgrApp.DoesNotExist as e:
                # we couldn't determine a BadgrApp from the referer, default to legacy frontend
                url = reverse("legacy_confirm_email", args=[emailconfirmation.key])
                ret = build_absolute_uri(request, url, protocol=app_settings.DEFAULT_HTTP_PROTOCOL)
                return ret
        return super(BadgrAccountAdapter, self).get_email_confirmation_url(request, emailconfirmation)

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
        if signup:
            email_template = 'account/email/email_confirmation_signup'
        else:
            email_template = 'account/email/email_confirmation'
        get_adapter().send_mail(email_template,
                                emailconfirmation.email_address.email,
                                ctx)
