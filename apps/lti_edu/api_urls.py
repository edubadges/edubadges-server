from django.conf.urls import url
from lti_edu.api import LTIStudentsEnrolledDetail
urlpatterns = [
    url(r'^enroll/(?P<eduID>[^/]+)$', LTIStudentsEnrolledDetail.as_view(), name='api_lti_edu_enroll_student'),
 ]