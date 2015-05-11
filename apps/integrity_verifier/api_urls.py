from django.conf.urls import patterns, url

from .api import VerifyBadgeInstanceView

urlpatterns = patterns(
    'issuer.api_views',
    url(r'^$', VerifyBadgeInstanceView.as_view(), name='verify_instance')
)
