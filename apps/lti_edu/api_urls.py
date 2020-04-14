from django.conf.urls import url
from lti_edu.api import BadgeClassLtiContextListView, CurrentContextView, BadgeClassLtiContextDetailView, \
    BadgeClassLtiContextStudentListView
from lti_edu.api import StudentsEnrolledList, StudentEnrollmentList, EnrollmentDetail

urlpatterns = [
    url(r'^enroll$', StudentsEnrolledList.as_view(), name='api_lti_edu_enroll_student'),
    url(r'^student/enrollments', StudentEnrollmentList.as_view(), name='api_lti_edu_student_enrollment_list'),
    url(r'^enrollment/(?P<entity_id>[^/]+)/deny', EnrollmentDetail.as_view(), name='api_lti_edu_update_enrollment'),

    url(r'^badgeclasslticontext/(?P<lti_context_id>[^/]+)', BadgeClassLtiContextListView.as_view(), name='badgeclasslticontext_list'),
    url(r'^badgeclasslticontextstudent/(?P<lti_context_id>[^/]+)', BadgeClassLtiContextStudentListView.as_view(),
        name='badgeclasslticontextstudent_list'),
    url(r'^addbadgeclasslticontext', BadgeClassLtiContextDetailView.as_view(), name='badgeclasslticontext_add'),
    url(r'^lticontext', CurrentContextView.as_view(), name='lticontext'),
 ]


