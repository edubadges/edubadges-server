import base64
import time

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.shortcuts import redirect
from django.template import loader, TemplateDoesNotExist, Context
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import EmailBlacklist


##
#
#  Error Handler Views
#
##
@xframe_options_exempt
def error404(request):
    try:
        template = loader.get_template('error/404.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Page not found (404)</h1>', content_type='text/html')
    return HttpResponseNotFound(template.render(Context({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    })))


@xframe_options_exempt
def error500(request):
    try:
        template = loader.get_template('error/500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return HttpResponseServerError(template.render(Context({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    })))


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


class AppleAppSiteAssociation(APIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (AllowAny,)

    def get(self, request):
        data = {
            "applinks": {
                "apps": [],
                "details": []
            }
        }

        for app_id in getattr(settings, 'APPLE_APP_IDS', []):
            data['applinks']['details'].append(app_id)

        return Response(data=data)
