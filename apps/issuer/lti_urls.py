from django.conf.urls import url

from issuer.lti_views import TestLti

urlpatterns = [

    url(r'^test_lti$', TestLti.as_view(), name='test_lti_view'),
]