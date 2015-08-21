import base64
import time

from django.db import IntegrityError
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import SimpleTemplateResponse
from django.views.generic import TemplateView

from .models import EmailBlacklist


class SitemapView(TemplateView):
    template_name = 'sitemap.html'


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


@login_required(
    login_url=getattr(
        settings, 'ROOT_INFO_REDIRECT',
        getattr(settings, 'LOGIN_URL', '/login')
    ),
    redirect_field_name=None
)
def info_view(request):
    return redirect(getattr(settings, 'LOGIN_REDIRECT_URL'))


def email_unsubscribe(request, *args, **kwargs):
    if time.time() > int(kwargs['expiration']):
        return HttpResponse('Your unsubscription link has expired.')

    try:
        email = base64.b64decode(kwargs['email_encoded'])
    except TypeError:
        return HttpResponse('Invalid unsubscribe link.')

    if not EmailBlacklist.verify_email_signature(**kwargs):
        return HttpResponse('Invalid unsubscribe link.')

    blacklist_instance = EmailBlacklist(email=email)
    try:
        blacklist_instance.save()
    except IntegrityError:
        pass

    return HttpResponse("You will no longer receive email notifications for \
                        earned badges from this domain.")
