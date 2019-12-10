from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect
from django.urls import reverse


class InactiveUserMiddleware(object):
#
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE_CLASSES setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the InactiveAccountMiddleware class.")
        if (request.user.is_authenticated and
            request.user.is_active == False and
            request.path != reverse('account_enabled')):
                return HttpResponseRedirect(reverse('account_enabled'))
        return self.get_response(request)
