# Views for Issuer API endpoints (incoming requests to this application)
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from models import EarnerNotification
from serializers import EarnerNotificationSerializer


class EarnerNotificationList(APIView):
    """
    GET a list of notifications 
    or POST assertion url/recipient email to create a new notification
    """
    model = EarnerNotification

    def get(self, request):
        try:
            notifications = EarnerNotification.objects.all()
        except EarnerNotification.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EarnerNotificationSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new EarnerNotification as long as you know the right email address for the badge
        assertion, and the earner has not been previously notified.
        """
        data = {'url': request.data.get('url'), 'email': request.data.get('email')}
        serializer = EarnerNotificationSerializer(data=data)

        if serializer.is_valid():
            try:
                serializer.create()
            except Exception as e:
                return Response(e.message, status=status.HTTP_400_BAD_REQUEST)

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EarnerNotificationDetail(APIView):
    model = EarnerNotification

    def get(self, request):
        pass

    def post(self, request):
        pass
