from django.views.generic import TemplateView


class TestLti(TemplateView):
    template_name = "lti/test_lti.html"

    def get_context_data(self, **kwargs):
        context_data = super(TestLti, self).get_context_data(**kwargs)
        context_data['ltitest'] = 'yes lti test'
        return context_data

    def post(self, request,*args, **kwargs):
        post = request.POST
        return self.get(request, *args, **kwargs)
