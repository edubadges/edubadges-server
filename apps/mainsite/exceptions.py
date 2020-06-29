from rest_framework.exceptions import APIException
from rest_framework.serializers import ValidationError


class BadgrApiException400(APIException):

    def __init__(self, error_message, error_code):
        if not error_code:
            detail = {'An exception occurred'}
        else:
            detail = {'detail': 'validation_error',
                      'fields': {'error_message': error_message, 'error_code': error_code}}
        super(BadgrApiException400, self).__init__(detail)

    status_code = 400


class BadgrValidationError(ValidationError):

    status_code = 400

    def __init__(self, error_message, error_code):
        if not error_code:
            detail = {'An exception occurred'}
        else:
            detail = {'detail': 'validation_error',
                      'fields': {'error_message': error_message, 'error_code': error_code}}
        super(BadgrValidationError, self).__init__(detail)


class GraphQLException(Exception):
    pass