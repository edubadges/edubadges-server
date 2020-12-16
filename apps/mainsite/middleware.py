import json
import logging

from django import http
from django.utils.deprecation import MiddlewareMixin
from json.decoder import JSONDecodeError
from mainsite import settings

logger = logging.getLogger('Badgr.Debug')


class MaintenanceMiddleware(MiddlewareMixin):
    """Serve a temporary redirect to a maintenance url in maintenance mode"""
    def process_request(self, request):
        if request.method == 'POST':
            if getattr(settings, 'MAINTENANCE_MODE', False) is True and hasattr(settings, 'MAINTENANCE_URL'):
                return http.HttpResponseRedirect(settings.MAINTENANCE_URL)
            return None


class TrailingSlashMiddleware(MiddlewareMixin):
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
        logger.exception(str(exception))


class RequestResponseLoggerMiddleware(MiddlewareMixin):

    def process_request(self, request):
        if request.method in ['POST', 'PUT', 'PATCH']:
            request.req_body = request.body  # for later retrieval

    def process_response(self, request, response):
        # don't log static files or media files requests
        if not request.path.startswith('/static') and not request.path.startswith('/media'):
            request_log = {
                'method': request.method,
                'path': request.path,
                'scheme': request.scheme,
                'user': request.user,
            }
            response_log = {'status_code': response.status_code}
            if request.method == 'GET':
                request_log['GET'] = request.GET
            elif request.method in ['POST', 'PUT']:
                if request.path.startswith('/graphql'):
                    request_log['body'] = request.req_body
                else:
                    response_log['content'] = response.content
                    if not hasattr(request, 'sensitive_post_parameters'):
                        body = request.req_body
                        if body.startswith(b'------WebKitFormBoundary'):
                            body = 'Multipart message, removed from logging'
                        else:
                            if body:
                                try:
                                    body = json.loads(body)
                                    if dict == type(body):
                                        image = body.get('image', None)
                                        if image and image.startswith('data:image'):
                                            body['image'] = 'Image string removed for logging purposes'
                                except JSONDecodeError:
                                    pass  # is not json, copy the entire string
                        request_log['body'] = body
            logger.info({'Request/Response Cycle': {'request': request_log, 'response': response_log}})
        return response
