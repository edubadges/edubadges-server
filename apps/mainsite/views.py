import base64
import mimetypes
import time

from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.storage import default_storage
from django.db import IntegrityError
from django.http import FileResponse, HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseServerError
from django.template import TemplateDoesNotExist, loader
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView
from issuer.models import BadgeInstance
from mainsite.admin_actions import clear_cache, send_application_report
from mainsite.models import EmailBlacklist

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
    return HttpResponseNotFound(
        template.render(
            {
                'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
            }
        )
    )


@xframe_options_exempt
def error500(request):
    try:
        template = loader.get_template('error/500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return HttpResponseServerError(
        template.render(
            {
                'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
            }
        )
    )


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

    return HttpResponse(
        'You will no longer receive email notifications for \
                        earned badges from this domain.'
    )


class SitewideActionForm(forms.Form):
    ACTION_CLEAR_CACHE = 'CLEAR_CACHE'
    ACTION_SEND_APP_REPORT = 'SEND_APP_REPORT'

    ACTIONS = {
        ACTION_CLEAR_CACHE: clear_cache,
        ACTION_SEND_APP_REPORT: send_application_report,
    }
    CHOICES = ((ACTION_CLEAR_CACHE, 'Clear Cache'), (ACTION_SEND_APP_REPORT, 'Send application Report'))

    action = forms.ChoiceField(choices=CHOICES, required=True, label='Pick an action')
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
    """
    Serves media files with access control.
    Fetches files from S3 storage and proxies them through Django.
    """
    # Check access permissions for assertion images
    if 'assertion-' in path:
        try:
            assertion = BadgeInstance.objects.get(image=path)
        except BadgeInstance.DoesNotExist:
            return HttpResponseNotFound(content='File not found'.encode('utf-8'))

        # Check if the assertion is public or user has permission
        has_permission = False
        if assertion.public:
            has_permission = True
        elif request.user.is_authenticated:
            if request.user == assertion.user or request.user.get_permissions(assertion)['may_read']:
                has_permission = True

        if not has_permission:
            return HttpResponseForbidden()

    try:
        if not default_storage.exists(path):
            return HttpResponseNotFound(content='File not found'.encode('utf-8'))

        # Open the file from S3
        file_obj = default_storage.open(path, 'rb')

        # Determine content type
        content_type, _ = mimetypes.guess_type(path)
        if content_type is None:
            content_type = 'application/octet-stream'

        # Create a streaming response
        response = FileResponse(file_obj, content_type=content_type)

        # Set content disposition for downloads
        response['Content-Disposition'] = f'inline; filename="{path.split("/")[-1]}"'

        return response

    except Exception as e:
        return HttpResponseServerError(content=f'Error serving file: {str(e)}'.encode('utf-8'))
