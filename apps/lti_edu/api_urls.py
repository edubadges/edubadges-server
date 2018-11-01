from django.conf.urls import url
from lti_edu.api import StudentsEnrolledList, CheckIfStudentIsEnrolled, StudentEnrollmentList
urlpatterns = [
    url(r'^enroll$', StudentsEnrolledList.as_view(), name='api_lti_edu_enroll_student'),
    url(r'^withdraw', StudentEnrollmentList.as_view(), name='api_lti_edu_withdraw_student'),
    url(r'^enrolledstudents/(?P<badgeclass_slug>[^/]+)$', StudentsEnrolledList.as_view(), name='api_lti_edu_enrolled_students'),
    url(r'^isstudentenrolled', CheckIfStudentIsEnrolled.as_view(), name='api_lti_is_student_enrolled'),
    url(r'^student/(?P<eduID>[^/]+)/enrollments', StudentEnrollmentList.as_view(), name='v2_api_student_badgeclass_list'),
 ]