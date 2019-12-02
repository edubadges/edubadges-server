from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.http import HttpResponseRedirect


# class InactiveUserMiddleware(object):
#     def process_request(self, request):
#         if not hasattr(request, 'user'):
#             raise ImproperlyConfigured(
#                 "The Django remote user auth middleware requires the"
#                 " authentication middleware to be installed.  Edit your"
#                 " MIDDLEWARE_CLASSES setting to insert"
#                 " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
#                 " before the InactiveAccountMiddleware class.")
#         if (request.user.is_authenticated() and
#             request.user.is_active == False and
#             request.path != reverse('account_enabled')):
#                 return HttpResponseRedirect(reverse('account_enabled'))
