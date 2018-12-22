# encoding: utf-8
from __future__ import unicode_literals

import datetime

from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import CachedEmailAddress
from badgeuser.serializers_v1 import EmailSerializerV1
from institution.serializers_v1 import FacultySerializerV1
from institution.models import Faculty
from apispec_drf.decorators import apispec_list_operation, apispec_post_operation, apispec_operation, \
    apispec_get_operation, apispec_delete_operation, apispec_put_operation

class BadgeUserFacultyList(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    
    @apispec_list_operation('BadgeUserFaculty',
        summary="Get a list of user's faculties",
        tags=['BadgeUsers']
    )
    def get(self, request, **kwargs):
        instances = request.user.faculty.all()
        if request.user.has_perm('badgeuser.has_institution_scope'): # add institution faculties
            instances = instances | Faculty.objects.filter(institution = request.user.institution)
        serializer = FacultySerializerV1(instances, many=True, context={'request': request})
        return Response(serializer.data)
    

RATE_LIMIT_DELTA = datetime.timedelta(minutes=5)

class BadgeUserEmailList(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @apispec_list_operation('BadgeUserEmail',
        summary="Get a list of user's registered emails",
        tags=['BadgeUsers']
    )
    def get(self, request, **kwargs):
        instances = request.user.cached_emails()
        serializer = EmailSerializerV1(instances, many=True, context={'request': request})
        return Response(serializer.data)

    @apispec_operation(
        summary="Register a new unverified email",
        tags=['BadgeUsers'],
        properties=[
            {
                'in': 'formData',
                'name': "email",
                'type': "string",
                'format': "email",
                'description': 'The email to register'
            }
        ]
    )
    def post(self, request, **kwargs):
        serializer = EmailSerializerV1(data=request.data, context={'request': request})
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

    @apispec_get_operation('BadgeUserEmail',
        summary="Get detail for one registered email",
        tags=['BadgeUsers']
    )
    def get(self, request, id, **kwargs):
        email_address = self.get_email(pk=id)
        if email_address is None or email_address.user_id != self.request.user.id:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EmailSerializerV1(email_address, context={'request': request})
        return Response(serializer.data)

    @apispec_delete_operation('BadgeUserEmail',
        summary="Remove a registered email for the current user",
        tags=['BadgeUsers']
    )
    def delete(self, request, id, **kwargs):
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

    @apispec_put_operation('BadgeUserEmail',
        summary='Update a registered email for the current user',
        tags=['BadgeUsers']
    )
    def put(self, request, id, **kwargs):
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
                send_confirmation = False
                current_time = datetime.datetime.now()
                last_request_time = email_address.get_last_verification_sent_time()

                if last_request_time is None:
                    email_address.set_last_verification_sent_time(datetime.datetime.now())
                    send_confirmation = True
                else:
                    time_delta = current_time - last_request_time
                    if time_delta > RATE_LIMIT_DELTA:
                        send_confirmation = True

                if send_confirmation:
                    email_address.send_confirmation(request=request)
                    email_address.set_last_verification_sent_time(datetime.datetime.now())
                else:
                    remaining_time_obj = RATE_LIMIT_DELTA - (datetime.datetime.now() - last_request_time)
                    remaining_min = (remaining_time_obj.seconds//60)%60
                    remaining_sec = remaining_time_obj.seconds%60
                    remaining_time_rep = "{} minutes and {} seconds".format(remaining_min, remaining_sec)

                    return Response("Will be able to re-send verification email in %s." % (str(remaining_time_rep)),
                     status=status.HTTP_429_TOO_MANY_REQUESTS)


        serializer = EmailSerializerV1(email_address, context={'request': request})
        serialized = serializer.data
        return Response(serialized, status=status.HTTP_200_OK)
