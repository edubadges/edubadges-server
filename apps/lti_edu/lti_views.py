from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from badgrsocialauth.utils import set_session_badgr_app
from mainsite.models import BadgrApp


class LoginLti(TemplateView):
    template_name = "lti/test_lti.html"

    def get_context_data(self, **kwargs):
        context_data = super(LoginLti, self).get_context_data(**kwargs)
        context_data['ltitest'] = 'yes lti test'
        badgr_app = BadgrApp.objects.get_current(request=self.request)
        if badgr_app is not None:
            set_session_badgr_app(self.request, badgr_app)
        if not self.request.user.is_authenticated():
            context_data['login_url'] = reverse('edu_id_login')
        return context_data

    def post(self, request,*args, **kwargs):
        post = request.POST

        return self.get(request, *args, **kwargs)
