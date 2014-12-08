from django.conf.urls import patterns, url
from issuer.views import *

urlpatterns = patterns('certificates.views',
    url(r'/create$', IssuerCreate.as_view(), name='issuer_create'),
    url(r'/(?P<pk>\d+)', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'/notify$', EarnerNotificationCreate.as_view(), name='notify_earner')
)
