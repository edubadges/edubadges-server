# encoding: utf-8
from __future__ import unicode_literals

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CachedEmailAddress
from .serializers import EmailSerializer


class BadgeUserEmailList(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        """
        Get a list of user's registered emails.
        ---
        serializer: EmailSerializer
        """
        instances = request.user.cached_emails()
        serializer = EmailSerializer(instances, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        """
        Register a new unverified email.
        ---
        serializer: EmailSerializer
        parameters:
            - name: email
              description: The email to register
              required: true
              type: string
              paramType: form
        """
        serializer = EmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        email_address = serializer.save(user=request.user)
        email = serializer.data
        email_address.send_confirmation(request)
        return Response(email, status=status.HTTP_201_CREATED)


class BadgeUserEmailView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get_email(self, **kwargs):
        try:
            email_address = CachedEmailAddress.cached.get(**kwargs)
        except CachedEmailAddress.DoesNotExist:
            return None
        else:
            return email_address

class BadgeUserEmailDetail(BadgeUserEmailView):
    model = CachedEmailAddress

    def get(self, request, id):
        """
        Get detail for one registered email.
        ---
        serializer: EmailSerializer
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
        """
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != self.request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = EmailSerializer(email_address, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, id):
        """
        Remove a registered email for the current user.
        ---
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
        """
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if email_address.primary:
            return Response({'error': "Can not remove primary email address"}, status=status.HTTP_400_BAD_REQUEST)

        if self.request.user.emailaddress_set.count() == 1:
            return Response({'error': "Can not remove only email address"}, status=status.HTTP_400_BAD_REQUEST)

        email_address.delete()
        return Response(status.HTTP_200_OK)

    def put(self, request, id):
        """
        Update a registered email for the current user.
        serializer: EmailSerializer
        ---
        parameters:
            - name: id
              type: string
              paramType: path
              description: the id of the registered email
              required: true
            - name: primary
              type: boolean
              paramType: form
              description: Should this email be primary contact for the user
              required: false
            - name: resend
              type: boolean
              paramType: form
              description: Request the verification email be resent
              required: false
        """
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if email_address.verified:
            if request.data.get('primary'):
                email_address.set_as_primary()
                email_address.publish()
        else:
            if request.data.get('resend'):
                email_address.send_confirmation(request=request)

        serializer = EmailSerializer(email_address, context={'request': request})
        serialized = serializer.data
        return Response(serialized, status=status.HTTP_200_OK)
