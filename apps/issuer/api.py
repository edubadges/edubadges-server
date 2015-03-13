# Views for Issuer API endpoints (incoming requests to this application)
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.db.models.query import EmptyQuerySet
from django.utils.text import slugify

from rest_framework import status, authentication, permissions
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from mainsite.renderers import JSONLDRenderer
from models import EarnerNotification, Issuer, IssuerBadgeClass, IssuerAssertion
from serializers import EarnerNotificationSerializer, IssuerSerializer, IssuerBadgeClassSerializer, IssuerAssertionSerializer


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


class IssuerList(APIView):
    """
    GET a list of issuers the current user is owner, editor or staff open
    or POST to create a new Issuer, which the requesting user will be owner of
    """
    model = Issuer

    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )

    def get(self, request):

        if not isinstance(request.user, get_user_model()):
            # TODO consider changing this a public API of all issuers (that are public?)
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Get the Issuers this user owns, edits, or staffs:
        user_issuers = Issuer.objects.filter(
            Q(owner__id=request.user.id) |
            Q(editors__id=request.user.id) |
            Q(staff__id=request.user.id)
        )
        if not user_issuers.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = IssuerSerializer(user_issuers, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """
        Define a new issuer owned by the authenticated user
        resuest.data = {
            "image" (optional)
            "description"
            "name"
            "slug" (optional)
            "url": "http://string"  # Organization's homepage (if not included, use local detail view),
            "email": "email@email.com"  # should be one of user's verified emails
        }
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        input_data = {
            'url': request.data.get('url'),
            'name': request.data.get('name'),
            'slug': slugify(request.data.get('slug', request.data.get('name'))),
        }
        if request.data.get('image') is not None:
            input_data['image'] = request.data.get('image')

        serializer = IssuerSerializer(data=input_data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        # Pass in user values where we have a real user object instead of a url
        # and non-model-field data to go into badge_object
        serializer.save(
            owner=request.user, 
            created_by=request.user, 
            description=request.data.get('description')
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class IssuerDetail(APIView):
    """
    GET details on one issuer. PUT and DELETE should be highly restricted operations and are not implemented yet
    """
    model = Issuer

    def get(self, request, slug):
        try:
            current_issuer = Issuer.objects.get(slug=slug)
        except Issuer.ObjectNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = IssuerSerializer(current_issuer, context={'request': request})
            return Response(serializer.data)


class IssuerBadgeObject(APIView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer
    renderer_classes = (JSONRenderer, JSONLDRenderer, )

    def get(self, request, slug):
        try:
            current_issuer = Issuer.objects.get(slug=slug)
        except Issuer.ObjectNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            return Response(current_issuer.badge_object)

