# encoding: utf-8


import datetime

from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from badgeuser.models import CachedEmailAddress
from badgeuser.serializers import EmailSerializer
from mainsite.exceptions import BadgrApiException400
from mainsite.utils import EmailMessageMaker, send_mail

RATE_LIMIT_DELTA = datetime.timedelta(minutes=5)


class BadgeUserEmailList(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, **kwargs):
        instances = request.user.cached_emails()
        serializer = EmailSerializer(instances, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, **kwargs):
        serializer = EmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        try:  # check if email already exists
            CachedEmailAddress.objects.get(email=request.data.get('email'), verified=1)
            raise BadgrApiException400("Could not register email address. Address already in use", 101)
        except CachedEmailAddress.DoesNotExist:
            try:
                CachedEmailAddress.objects.get(email=request.data.get('email'), verified=0, user_id=request.user.pk)
                raise BadgrApiException400("You have already added this address. Verify it", 102)
            except CachedEmailAddress.DoesNotExist:
                pass
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

    def get(self, request, id, **kwargs):
        email_address = self.get_email(pk=id)
        if email_address is None or email_address.user_id != self.request.user.id:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EmailSerializer(email_address, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, id, **kwargs):
        email_address = self.get_email(pk=id)
        if email_address is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if email_address.user_id != request.user.id:
            return Response(status=status.HTTP_403_FORBIDDEN)

        if email_address.primary:
            raise BadgrApiException400("Can not remove primary email address", 103)

        if self.request.user.emailaddress_set.count() == 1:
            raise BadgrApiException400("Can not remove only email address", 104)

        email_address.delete()
        return Response(status.HTTP_200_OK)

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
        elif request.data.get('resend'):
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
                remaining_min = (remaining_time_obj.seconds // 60) % 60
                remaining_sec = remaining_time_obj.seconds % 60
                remaining_time_rep = "{} minutes and {} seconds".format(remaining_min, remaining_sec)

                return Response("Will be able to re-send verification email in %s." % (str(remaining_time_rep)),
                                status=status.HTTP_429_TOO_MANY_REQUESTS)
        else:
            raise BadgrApiException400("Can't make unverified email address the primary email address", 105)

        serializer = EmailSerializer(email_address, context={'request': request})
        serialized = serializer.data
        return Response(serialized, status=status.HTTP_200_OK)


class FeedbackView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, **kwargs):
        message = request.data['message']
        html_message = EmailMessageMaker.create_feedback_mail(request.user, message)
        send_mail(subject='Feedback',
                  message=message,
                  html_message=html_message,
                  recipient_list=[settings.REPORT_RECEIVER_EMAIL])
        return Response({}, status=status.HTTP_201_CREATED)
