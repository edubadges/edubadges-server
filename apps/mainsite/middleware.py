from django import http
from mainsite import settings


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
        if filter(request.path.startswith, exceptions):
            if request.path[-1] != '/':
                return http.HttpResponsePermanentRedirect(request.path+"/")
        else:
            if request.path != '/' and request.path[-1] == '/':
                return http.HttpResponsePermanentRedirect(request.path[:-1])
        return None
