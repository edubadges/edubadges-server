from django.conf.urls import patterns, url
from issuer.public_api import *

urlpatterns = patterns(
   'issuer.public_api_views',
   url(r'^/issuers/(?P<slug>[\-0-9a-z]+)$', IssuerBadgeObject.as_view(), name='issuer_badge_object'),

   url(r'^/badges/(?P<slug>[\-0-9a-z]+)$', IssuerBadgeClassObject.as_view(), name='badgeclass_badge_object'),
   url(r'^/badges/(?P<slug>[\-0-9a-z]+)/image', IssuerBadgeClassImage.as_view(), name='badgeclass_image'),
   url(r'^/badges/(?P<slug>[\-0-9a-z]+)/criteria', IssuerBadgeClassCriteria.as_view(), name='badgeclass_criteria'),

   url(r'^/assertions/(?P<slug>[\-0-9a-z]+)$', IssuerAssertionBadgeObject.as_view(), name='assertion_badge_object'),
   url(r'^/assertions/(?P<slug>[\-0-9a-z]+)/image', IssuerAssertionImage.as_view(), name='assertion_image'),

)
