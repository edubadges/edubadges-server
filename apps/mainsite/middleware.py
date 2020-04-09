import logging
from django import http
from mainsite import settings

logger = logging.getLogger('Badgr.Debug')


class MaintenanceMiddleware(object):
    """Serve a temporary redirect to a maintenance url in maintenance mode"""
    def process_request(self, request):
        if request.method == 'POST':
            if getattr(settings, 'MAINTENANCE_MODE', False) is True and hasattr(settings, 'MAINTENANCE_URL'):
                return http.HttpResponseRedirect(settings.MAINTENANCE_URL)
            return None


class TrailingSlashMiddleware(object):
    def process_request(self, request):
        """Removes the slash from urls, or adds a slash for the admin urls"""
        exceptions = ['/staff', '/__debug__']
        if list(filter(request.path.startswith, exceptions)):
            if request.path[-1] != '/':
                return http.HttpResponsePermanentRedirect(request.path+"/")
        else:
            if request.path != '/' and request.path[-1] == '/':
                return http.HttpResponsePermanentRedirect(request.path[:-1])
        return None


class ExceptionHandlerMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        logger.error(str(exception))
