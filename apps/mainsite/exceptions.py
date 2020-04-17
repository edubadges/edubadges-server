from rest_framework.exceptions import APIException


class BadgrApiException400(APIException):

    def __init__(self, fields):
        detail = {'detail': 'bad_request', 'fields': fields}
        super(BadgrApiException400, self).__init__(detail)

    status_code = 400


class BadgrValidationError(APIException):

    status_code = 400

    def __init__(self, fields):
        detail = {'detail': 'validation_error', 'fields': fields}
        super(BadgrValidationError, self).__init__(detail)


class GraphQLException(Exception):
    pass