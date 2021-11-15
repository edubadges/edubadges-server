from django.conf.urls import url
from lti_edu.api import StudentsEnrolledList, StudentEnrollmentList, EnrollmentDetail

urlpatterns = [
    url(r'^enroll$', StudentsEnrolledList.as_view(), name='api_lti_edu_enroll_student'),
    url(r'^student/enrollments', StudentEnrollmentList.as_view(), name='api_lti_edu_student_enrollment_list'),
    url(r'^enrollment/(?P<entity_id>[^/]+)/deny', EnrollmentDetail.as_view(), name='api_lti_edu_update_enrollment'),

]
