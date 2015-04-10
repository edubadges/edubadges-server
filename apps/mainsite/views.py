from django import http
from django import template
from django.shortcuts import redirect

from django.conf import settings
# from django.core.urlresolvers import reverse
from django.template.response import SimpleTemplateResponse
from django.views.generic.base import TemplateView
from django.contrib.auth import authenticate, login, logout


class ActiveTabMixin(object):
    def get_context_data(self, **kwargs):
        context = super(ActiveTabMixin, self).get_context_data(**kwargs)
        context['active_tab'] = self.active_tab
        return context 


class SitemapView(ActiveTabMixin, TemplateView):
    template_name = 'sitemap.html'
    active_tab = 'home'

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
    response_class = SimpleTemplateResponse  # Doesn't call context_processors (which could be where the 500 came from in the first place)

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

