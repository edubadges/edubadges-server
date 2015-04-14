from django.conf.urls import patterns, url
from views import IssuerPortal

urlpatterns = patterns('contact.views',
    url(r'^', IssuerPortal.as_view(), name='issuer_portal'),
)
