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


class BadgrValidationFieldError(BadgrValidationError):
    """Error to use when throwing an exception on a specific field in the form."""

    status_code = 400

    def __init__(self, field_name, error_message, error_code):
        error_message = {field_name: [{'error_message': error_message,
                                       'error_code': error_code}]}
        super(BadgrValidationFieldError, self).__init__(error_message, 999)


class GraphQLException(Exception):
    pass