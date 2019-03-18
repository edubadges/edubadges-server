from django.conf.urls import url

from lti_edu.lti_views import LoginLti

urlpatterns = [

    url(r'^test_lti$', LoginLti.as_view(), name='test_lti_view'),
]