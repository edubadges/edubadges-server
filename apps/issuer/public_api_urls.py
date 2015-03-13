from django.conf.urls import patterns, url
from issuer.api import *

urlpatterns = patterns('issuer.public_api_views',
   url(r'^/issuers/(?P<slug>[\-0-9a-z]+)$', IssuerBadgeObject.as_view(), name='issuer_badge_object'),
)
