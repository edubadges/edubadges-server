import json

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template.response import SimpleTemplateResponse
from django.views.generic import TemplateView

from .serializers import UserViewDataSerializer


class SitemapView(TemplateView):
    template_name = 'sitemap.html'


class ApplicationPortal(TemplateView):
    template_name = 'base_interior.html'

    def get(self, request):
        if not request.user.is_authenticated():
            return redirect(reverse('login'))

        context = self.get_context_data(**{'request': request})
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context_data = super(ApplicationPortal, self).get_context_data(**kwargs)
        user_serializer = UserViewDataSerializer(kwargs['request'].user, context=kwargs)

        context_data['initial_data'] = json.dumps(user_serializer.data)

        return context_data


##
#
#  Error Handler Views
#
##
class Error404(TemplateView):
    template_name = '404.html'

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({'status': 404})
        return super(Error404, self).render_to_response(context, **response_kwargs)
error404 = Error404.as_view()


class Error500(TemplateView):
    template_name = '500.html'
    response_class = SimpleTemplateResponse  # Doesn't call context_processors (possible 500 error source)

    def get_context_data(self, **kwargs):
        # We must add STATIC_URL manually because context_processors aren't being called
        return {
            'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
        }

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update({'status': 500})
        return self.response_class(
            template=self.get_template_names(),
            context=context,
            **response_kwargs
        )
error500 = Error500.as_view()
