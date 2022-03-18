import threading

from django.shortcuts import get_object_or_404
from django.utils import timezone
from lxml.etree import strip_tags
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from entity.api import BaseEntityListView, BaseEntityDetailView
from issuer.models import BadgeClass
from lti_edu.models import StudentsEnrolled
from lti_edu.serializers import StudentsEnrolledSerializerWithRelations
from mainsite.exceptions import BadgrApiException400, BadgrValidationError
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail
from notifications.models import BadgeClassUserNotification
from staff.permissions import HasObjectPermission


class StudentEnrollmentList(BaseEntityListView):
    """
    GET a list of enrollments for a student
    DELETE for a student to delete your own enrollment
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    model = StudentsEnrolled
    serializer_class = StudentsEnrolledSerializerWithRelations
    http_method_names = ['get', 'delete']

    def get_objects(self, request, **kwargs):
        return StudentsEnrolled.objects.filter(user=request.user)

    def get(self, request, **kwargs):
        return super(StudentEnrollmentList, self).get(request, **kwargs)

    def delete(self, request, **kwargs):
        try:
            enrollment = StudentsEnrolled.objects.get(entity_id=request.data['enrollmentID'])
        except ValueError:
            raise BadgrApiException400("Invalid enrollment id", 204)
        except StudentsEnrolled.DoesNotExist:
            raise BadgrApiException400("Enrollment not found", 205)
        else:
            if enrollment.date_awarded:
                raise BadgrApiException400("Awarded enrollments cannot be withdrawn", 206)
            if request.user == enrollment.user:
                enrollment.delete()
                return Response(data='Enrollment withdrawn', status=200)
            else:
                raise BadgrApiException400("Users can only withdraw their own enrollments", 207)


class StudentsEnrolledList(BaseEntityListView):
    """
    POST: for a student to enroll himself
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    model = StudentsEnrolled
    http_method_names = ['post']

    def post(self, request, **kwargs):
        if 'badgeclass_slug' not in request.data:
            raise BadgrApiException400("Missing badgeclass id", 208)
        badge_class = get_object_or_404(BadgeClass, entity_id=request.data['badgeclass_slug'])
        if not badge_class.terms_accepted(request.user):
            raise BadgrValidationError("Cannot enroll, must accept terms first", 0)
        if request.user.may_enroll(badge_class, raise_exception=True):
            enrollment = StudentsEnrolled.objects.create(
                badge_class_id=badge_class.pk,
                user=request.user,
                narrative=request.data.get("narrative"),
                evidence_url=request.data.get("evidence_url"),
                date_consent_given=timezone.now()
            )
            # Clear cache for the enrollments of this badgeclass
            badge_class.remove_cached_data(['cached_pending_enrollments'])
            badge_class.remove_cached_data(['cached_pending_enrollments_including_denied'])
            message = EmailMessageMaker.create_student_badge_request_email(request.user, badge_class)
            request.user.email_user(subject='You have successfully requested an edubadge', html_message=message)

            # Send notifications to all users who have indicated they want to get notified
            def send_notifications(badge_class, created_enrollment):
                user_notifications = BadgeClassUserNotification.objects.filter(badgeclass=badge_class).all()
                for user_notification in user_notifications:
                    perms = badge_class.get_permissions(user_notification.user)
                    if perms['may_sign']:
                        html_message = EmailMessageMaker.create_enrolment_notification_mail(badge_class,
                                                                                            request.user,
                                                                                            created_enrollment)
                        send_mail(subject='Een edubadge is aangevraagd! An edubadge is requested!',
                                  message=None, html_message=html_message,
                                  recipient_list=[user_notification.user.email])
                    else:
                        user_notification.delete()

            thread = threading.Thread(target=send_notifications, args=(badge_class, enrollment))
            thread.start()
            return Response(data={'status': 'enrolled', 'entity_id': enrollment.entity_id}, status=201)
        raise BadgrApiException400('Cannot enroll', 209)


class EnrollmentDetail(BaseEntityDetailView):
    """
    PUT: update enrollment
    """
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    permission_map = {'PUT': 'may_award'}
    model = StudentsEnrolled
    http_method_names = ['put']

    def put(self, request, **kwargs):
        enrollment = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, enrollment):
            raise BadgrApiException400("You do not have permission", 210)
        if enrollment.denied:
            raise BadgrApiException400("Enrollment already denied", 211)
        if enrollment.badge_instance:
            raise BadgrApiException400("Awarded enrollments cannot be denied", 212)
        enrollment.denied = True
        enrollment.deny_reason = request.data['denyReason']
        enrollment.save()
        html_message = EmailMessageMaker.create_enrollment_denied_email(enrollment)
        subject = 'Your request for the badgeclass {} has been denied by the issuer.'.format(
            enrollment.badge_class.name)
        enrollment.user.email_user(subject=subject, html_message=html_message)
        # Clear cache for the enrollments of this badgeclass
        enrollment.badge_class.remove_cached_data(['cached_pending_enrollments'])
        enrollment.badge_class.remove_cached_data(['cached_pending_enrollments_including_denied'])
        return Response(data='Succesfully denied enrollment', status=HTTP_200_OK)
