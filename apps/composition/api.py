from rest_framework import permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from django.core.exceptions import ValidationError as DjangoValidationError

from mainsite.permissions import IsOwner
from local_components.models import BadgeInstance as LocalBadgeInstance

from .serializers import (LocalBadgeInstanceSerializer,
                          LocalBadgeInstanceUploadSerializer)
#from .models import Collection, LocalBadgeInstanceCollection


class LocalBadgeInstanceList(APIView):
    """
    Retrieve a list of user's earned badges or post a new badge.
    """
    queryset = LocalBadgeInstance.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request):
        """
        GET a list of all the logged-in user's earned badges
        ---
        serializer: LocalBadgeInstanceSerializer
        """
        user_badges = self.queryset.filter(recipient_user=request.user)
        serializer = LocalBadgeInstanceSerializer(
            user_badges, many=True, context={
                'request': request,
                'format': request.query_params.get('json_format', 'v1')
            }
        )

        return Response(serializer.data)

    def post(self, request):
        """
        POST badge information to add a badge to the logged-in user's account.
        Badgealong with either a badge image file, hosted
        badge assertion URL, or badge assertion content itself.
        ---
        serializer: LocalBadgeInstanceUploadSerializer
        parameters:
            - name: image
              description: A baked badge image file
              required: false
              type: file
              paramType: form
            - name: assertion
              description: The signed or hosted assertion content, either as a JSON string or base64-encoded JWT
              required: false
              type: string
              paramType: form
            - name: url
              description: The URL of a hosted assertion
              required: false
              type: string
              paramType: form
        """
        serializer = LocalBadgeInstanceUploadSerializer(
            data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
