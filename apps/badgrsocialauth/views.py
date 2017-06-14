from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseBadRequest
from django.views.generic import RedirectView

from badgrsocialauth.utils import set_url_query_params
from mainsite.models import BadgrApp


class BadgrSocialLogin(RedirectView):
    def get(self, request, *args, **kwargs):
        try:
            logout(request)
            return super(BadgrSocialLogin, self).get(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseBadRequest(e.message)

    def get_redirect_url(self):
        final_redirect_url = BadgrApp.objects.get_current().ui_login_redirect

        if final_redirect_url is not None:
            self.request.session['final_redirect_url'] = final_redirect_url

        provider_name = self.request.GET.get('provider', None)

        if provider_name is None:
            raise ValidationError('No provider specified')

        try:
            return reverse('{}_login'.format(self.request.GET.get('provider')))
        except NoReverseMatch:
            raise ValidationError('No {} provider found'.format(provider_name))


class BadgrSocialAccountSignup(RedirectView):
    def get_redirect_url(self):
        final_redirect_url = self.request.session.get('final_redirect_url', None)
        if final_redirect_url is not None:
            return set_url_query_params(final_redirect_url, authError='An account already exists with provided email address')




class BadgrSocialAccountValidateEmail(RedirectView):
    def get_redirect_url(self):
        final_redirect_url = self.request.session.get('final_redirect_url', None)
        if final_redirect_url is not None:
            return set_url_query_params(final_redirect_url, authError='Please check your email address for a confirmation email')