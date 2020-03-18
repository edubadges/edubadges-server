from django.db.models import ProtectedError
from rest_framework import views, status
from rest_framework.response import Response


def exception_handler(exc, context):
    version = context.get('kwargs', None).get('version', 'v1')
    if version == 'v1':
        # Use the default exception-handling logic for v1
        if isinstance(exc, ProtectedError):
            description, protected_objects = exc.args
            return Response(description, status=status.HTTP_400_BAD_REQUEST)
        return views.exception_handler(exc, context)
