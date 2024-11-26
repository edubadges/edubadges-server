from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt

from lti13.api import LtiCourseDetail, LtiCourseDetailList
from lti13.views import login, launch, get_jwks, get_lti_context, get_members, get_grades

urlpatterns = [
    path("login/", csrf_exempt(login), name="lti_login"),
    path("launch/", csrf_exempt(launch), name="lti_launch"),
    path("jwks/", get_jwks, name="lti_jwks"),
    re_path(r"^context/(?P<launch_id>[\w-]+)/$", csrf_exempt(get_lti_context), name="lti_context"),
    re_path(r"^grades/(?P<launch_id>[\w-]+)/$", csrf_exempt(get_grades), name="lti_grades"),
    re_path(r"^members/(?P<launch_id>[\w-]+)/$", csrf_exempt(get_members), name="lti_members"),
    path("course/create", LtiCourseDetailList.as_view(), name="lti_course_create"),
    path("course/delete/<str:entity_id>", LtiCourseDetail.as_view(), name="lti_course_delete"),
]
