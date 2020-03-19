from rest_framework.exceptions import APIException


class BadgrApiException400(APIException):

    status_code = 400


class BadgrValidationError(APIException):

    status_code = 400

    def __init__(self, fields):
        detail = {'detail': 'validation_error', 'fields': fields}
        super(BadgrValidationError, self).__init__(detail)

