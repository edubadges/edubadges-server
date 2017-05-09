from django import http

import six
from django.db.models import ProtectedError
from rest_framework import views, exceptions, status
from rest_framework.response import Response

from entity.serializers import V2ErrorSerializer
from entity.authentication import CSRFPermissionDenied


def exception_handler(exc, context):
    version = context.get('kwargs', None).get('version', 'v1')
    if version == 'v1':
        # Use the default exception-handling logic for v1
        return views.exception_handler(exc, context)
    elif version == 'v2':
        description = 'miscellaneous error'
        field_errors = {}
        validation_errors = []
        response_code = None
        if isinstance(exc, exceptions.ParseError):
            description = 'bad request'
            validation_errors = [exc.detail]

        elif isinstance(exc, exceptions.ValidationError):
            description = 'bad request'

            if isinstance(exc.detail, list):
                validation_errors = exc.detail
            elif isinstance(exc.detail, dict):
                field_errors = exc.detail
            elif isinstance(exc.detail, six.string_types):
                validation_errors = [exc.detail]

            response_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
            description = 'no valid auth token found'
            response_code = status.HTTP_401_UNAUTHORIZED

        elif isinstance(exc, CSRFPermissionDenied):
            description = 'no valid csrf token found'
            response_code = status.HTTP_401_UNAUTHORIZED

        elif isinstance(exc, (http.Http404, exceptions.PermissionDenied)):
            description = 'entity not found or insufficient privileges'
            response_code = status.HTTP_404_NOT_FOUND

        elif isinstance(exc, ProtectedError):
            description, protected_objects = exc.args
            response_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(exc, exceptions.APIException):
            field_errors = exc.detail
            response_code = exc.status_code

        else:
            # Unrecognized exception, return 500 error
            return None


        serializer = V2ErrorSerializer(instance={},
                                       success=False,
                                       description=description,
                                       field_errors=field_errors,
                                       validation_errors=validation_errors)

        return Response(serializer.data, status=response_code)
