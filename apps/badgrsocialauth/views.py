import urllib
import urlparse

from allauth.socialaccount.providers.base import AuthProcess
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.generic import RedirectView
from rest_framework.exceptions import AuthenticationFailed

from badgrsocialauth.utils import set_url_query_params, set_session_badgr_app, get_session_badgr_app, \
    get_session_verification_email, set_session_authcode
from lti_edu.lti_views import logout_badgr_user
from mainsite.models import BadgrApp


class BadgrSocialLogin(RedirectView):
    def get(self, request, *args, **kwargs):
        try:
            lti_data = request.session.get('lti_data', None)
            logout(request)
            #logout_badgr_user(request, request.user)
            request.session['lti_data'] = lti_data
            return super(BadgrSocialLogin, self).get(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseBadRequest(e.message)
        except AuthenticationFailed as e:
            return HttpResponseForbidden(e.detail)

    def get_redirect_url(self):
        provider_name = self.request.GET.get('provider', None)
        if provider_name is None:
            raise ValidationError('No provider specified')

        badgr_app = BadgrApp.objects.get_current(request=self.request)
        if badgr_app is not None:
            set_session_badgr_app(self.request, badgr_app)
        else:
            raise ValidationError('Unable to save BadgrApp in session')

        try:
            redirect_url = reverse('{}_login'.format(self.request.GET.get('provider')))
        except NoReverseMatch:
            raise ValidationError('No {} provider found'.format(provider_name))

        authcode = self.request.GET.get('authCode', None)
        if authcode is not None:
            set_session_authcode(self.request, authcode)
            return set_url_query_params(redirect_url, process=AuthProcess.CONNECT)
        else:
            return redirect_url


class BadgrSocialLoginCancel(RedirectView):
    def get_redirect_url(self):
        badgr_app = get_session_badgr_app(self.request)
        if badgr_app is not None:
            return set_url_query_params(badgr_app.ui_login_redirect)


class BadgrSocialEmailExists(RedirectView):
    def get_redirect_url(self):
        badgr_app = get_session_badgr_app(self.request)
        if badgr_app is not None:
            return set_url_query_params(badgr_app.ui_login_redirect,
                                        authError='An account already exists with provided email address')


class BadgrSocialAccountVerifyEmail(RedirectView):
    def get_redirect_url(self):
        badgr_app = get_session_badgr_app(self.request)
        verification_email = get_session_verification_email(self.request)

        if verification_email is not None:
            verification_email = urllib.quote(verification_email.encode('utf-8'))
        else:
            verification_email = ''

        if badgr_app is not None:
            return urlparse.urljoin(badgr_app.ui_signup_success_redirect.rstrip('/') + '/', verification_email)


class BadgrAccountConnected(RedirectView):
    def get_redirect_url(self):
        badgr_app = get_session_badgr_app(self.request)
        if badgr_app is not None:
            return set_url_query_params(badgr_app.ui_connect_success_redirect)