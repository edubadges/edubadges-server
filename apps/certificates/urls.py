from django.conf.urls import patterns, url
from certificates.views import *

urlpatterns = patterns('certificates.views',
    url(r'^$', CertificateCreate.as_view(), name='certificate_create'),
    url(r'certificates/(?P<pk>\d+)',CertificateDetail.as_view(), name='certificate_detail')
)
