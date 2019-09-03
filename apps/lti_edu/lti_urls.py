from django.conf.urls import url
from django.views.generic import TemplateView

from lti_edu.lti_views import LoginLti, LoginLtiStaff, CheckLogin, CheckLoginAdmin

urlpatterns = [

    url(r'^lti$', LoginLti.as_view(), name='lti_view'),
    url(r'^check_login$', CheckLogin.as_view(), name='check-login'),
    url(r'^check_login_staff$', CheckLoginAdmin.as_view(), name='check-login-staff')
]