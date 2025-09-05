"""
HTTP endpoint for verifying the health of the Badgr API, as hosted on one server
Thanks to edx.org for endpoint design pattern. Licensed by edX under aGPL.
https://github.com/edx/ecommerce/blob/master/LICENSE.txt
"""
from django.db import connection, DatabaseError
from django.http import JsonResponse, HttpResponse
from rest_framework import status

OK = 'OK'
UNAVAILABLE = 'UNAVAILABLE'


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


def readiness(req):
    """
    Kubernetes readiness probe endpoint.
    
    This endpoint checks if the application is ready to serve requests by testing
    database connectivity. It returns a simple HTTP 200/503 status for easy
    consumption by Kubernetes readiness probes.
    
    Returns:
        HttpResponse: 200 if ready to serve requests (database accessible)
        HttpResponse: 503 if not ready (database unavailable)
    
    Example Kubernetes probe configuration:
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        return HttpResponse("Ready", status=200, content_type="text/plain")
    except DatabaseError:
        return HttpResponse("Not Ready - Database Unavailable", 
                          status=status.HTTP_503_SERVICE_UNAVAILABLE, 
                          content_type="text/plain")


def liveness(req):
    """
    Kubernetes liveness probe endpoint.
    
    This endpoint performs a simple aliveness check. It returns HTTP 200 if the
    application process is running and can handle requests. This is used by
    Kubernetes to determine if a pod should be restarted.
    
    Returns:
        HttpResponse: Always returns 200 if the process is running
    
    Example Kubernetes probe configuration:
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
    """
    return HttpResponse("Alive", status=200, content_type="text/plain")
