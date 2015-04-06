"""
HTTP endpoint for verifying the health of the Badge Trust API, as hosted on one server
Thanks to edx.org for endpoint design pattern.
"""
# import logger  # TODO integrate logging into results of health endpoint queries
# import requests  # use for making requests to any dependency HTTP APIs.
from rest_framework import status
from django.conf import settings
from django.db import connection, DatabaseError
from django.http import JsonResponse


OK = u'OK'
UNAVAILABLE = u'UNAVAILABLE'


def health(req):
    """
    Allows a load balancer to verify that the badges service is up and OK.

    Integrate checks on the database and any other service that this application depends on.

    Returns:
        HttpResponse: 200 if the badges service is available, with JSON data
            indicating the health of each dependency service.
        HttpResponse: 503 if the badges service is unavailable, with JSON data
            indicating the health of each dependency service
    Example:
        >>> response = requests.get('/health')
        >>> response.status_code
        200
        >>> response.content
        '{"overall_status": "OK", "detailed_status": {"database_status": "OK"}}'
    """
    overall_status = database_status = UNAVAILABLE

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        database_status = OK
    except DatabaseError:
        # logger.critical('Unable to connect to database')
        database_status = UNAVAILABLE

    overall_status = OK if (database_status == OK) else UNAVAILABLE

    data = {
        'overall_status': overall_status,
        'detailed_status': {
            'database_status': database_status
            # Future: Report any other dependency statuses here.
        }
    }

    if overall_status == OK:
        return JsonResponse(data)
    else:
        return JsonResponse(data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
