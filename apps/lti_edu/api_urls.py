from django.conf.urls import url
from lti_edu.api import LTIStudentsEnrolledDetail, LTICheckIfStudentIsEnrolled
urlpatterns = [
    url(r'^enroll$', LTIStudentsEnrolledDetail.as_view(), name='api_lti_edu_enroll_student'),
    url(r'^enrolledstudents/(?P<badgeclass_slug>[^/]+)$', LTIStudentsEnrolledDetail.as_view(), name='api_lti_edu_enrolled_students'),
    url(r'^isstudentenrolled', LTICheckIfStudentIsEnrolled.as_view(), name='api_lti_is_student_enrolled')
 ]