from django.core.urlresolvers import reverse
from django.views.generic import RedirectView

from mainsite.models import BadgrApp


class BadgrSocialLogin(RedirectView):
    def get_redirect_url(self):
        final_redirect_url = BadgrApp.objects.get_current().ui_login_redirect

        if final_redirect_url is not None:
            self.request.session['final_redirect_url'] = final_redirect_url

        return reverse('{}_login'.format(self.request.GET.get('provider')))