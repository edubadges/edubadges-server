import base64
import time

from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template import loader, TemplateDoesNotExist
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView, RedirectView
from django.views.static import serve

from issuer.models import BadgeInstance
from mainsite.admin_actions import clear_cache, send_application_report
from mainsite.models import EmailBlacklist, BadgrApp


##
#
#  Error Handler Views
#
##


@xframe_options_exempt
def error404(request, exception):
    try:
        template = loader.get_template('error/404.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Page not found (404)</h1>', content_type='text/html')
    return HttpResponseNotFound(template.render({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    }))


@xframe_options_exempt
def error500(request):
    try:
        template = loader.get_template('error/500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return HttpResponseServerError(template.render({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    }))

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


class SitewideActionForm(forms.Form):
    ACTION_CLEAR_CACHE = 'CLEAR_CACHE'
    ACTION_SEND_APP_REPORT = 'SEND_APP_REPORT'

    ACTIONS = {
        ACTION_CLEAR_CACHE: clear_cache,
        ACTION_SEND_APP_REPORT: send_application_report,
    }
    CHOICES = (
        (ACTION_CLEAR_CACHE, 'Clear Cache'),
        (ACTION_SEND_APP_REPORT, 'Send application Report')
    )

    action = forms.ChoiceField(choices=CHOICES, required=True, label="Pick an action")
    confirmed = forms.BooleanField(required=True, label='Are you sure you want to perform this action?')


class SitewideActionFormView(FormView):
    form_class = SitewideActionForm
    template_name = 'admin/sitewide_actions.html'
    success_url = reverse_lazy('admin:index')
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.user.is_superuser:
            return super(SitewideActionFormView, self).render_to_response(context, **response_kwargs)
        else:
            return HttpResponseForbidden()
        
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SitewideActionFormView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        action = form.ACTIONS[form.cleaned_data['action']]

        if hasattr(action, 'delay'):
            action.delay()
        else:
            action()

        return super(SitewideActionFormView, self).form_valid(form)


def serve_protected_document(request, path, document_root):
    if 'assertion-' in path:
        assertion = BadgeInstance.objects.get(image=path)
        if assertion.public:
            return serve(request, path, document_root)
        else:
            if request.user.is_authenticated:
                if request.user is assertion.user or request.user.get_permissions(assertion)['may_read']:
                    return serve(request, path, document_root)
        return HttpResponseForbidden()
    return serve(request, path, document_root)
