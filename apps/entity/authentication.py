from rest_framework import exceptions
from rest_framework.authentication import SessionAuthentication


class CSRFPermissionDenied(exceptions.PermissionDenied):
    pass


class ExplicitCSRFSessionAuthentication(SessionAuthentication):
    """
    Wrapper class that raises an explicit CSRFPermissionDenied on CSRF failure to facilitate custom behavior in
    entity.views.exception_handler.
    """
    def enforce_csrf(self, request):
        try:
            return super(ExplicitCSRFSessionAuthentication, self).enforce_csrf(request)
        except exceptions.PermissionDenied as e:
            raise CSRFPermissionDenied(e.detail)
