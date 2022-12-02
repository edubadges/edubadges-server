from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from lti13.api import LtiCourseDetail, LtiCourseDetailList
from lti13.views import login, launch, get_jwks, get_lti_context, get_members, get_grades

urlpatterns = [
    url(r'^login/$', csrf_exempt(login), name='lti_login'),
    url(r'^launch/$', csrf_exempt(launch), name='lti_launch'),
    url(r'^jwks/$', get_jwks, name='lti_jwks'),
    url(r'^context/(?P<launch_id>[\w-]+)/$', csrf_exempt(get_lti_context), name='lti_context'),
    url(r'^grades/(?P<launch_id>[\w-]+)/$', csrf_exempt(get_grades), name='lti_grades'),
    url(r'^members/(?P<launch_id>[\w-]+)/$', csrf_exempt(get_members), name='lti_members'),
    url(r'^course/create$', LtiCourseDetailList.as_view(), name='lti_course_create'),
    url(r'^course/delete/(?P<entity_id>[^/]+)$', LtiCourseDetail.as_view(), name='lti_course_delete'),
]
