from django.urls import path, re_path
from lti_edu.api import StudentsEnrolledList, StudentEnrollmentList, EnrollmentDetail

urlpatterns = [
    path("enroll", StudentsEnrolledList.as_view(), name="api_lti_edu_enroll_student"),
    re_path(r"^student/enrollments", StudentEnrollmentList.as_view(), name="api_lti_edu_student_enrollment_list"),
    re_path(r"^enrollment/(?P<entity_id>[^/]+)/deny", EnrollmentDetail.as_view(), name="api_lti_edu_update_enrollment"),
]
