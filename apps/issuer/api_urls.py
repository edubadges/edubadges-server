from django.conf.urls import patterns, url
from issuer.api import *

urlpatterns = patterns(
   'issuer.api_views',
   url(r'^/notifications$', EarnerNotificationList.as_view(), name='issuer_notifications_list'),
   url(r'^/notifications/(?P<pk>[0-9]+)$', EarnerNotificationDetail.as_view(), name='issuer_notification_detail'),

   url(r'^/issuers$', IssuerList.as_view(), name='issuer_list'),
   url(r'^/issuers/(?P<slug>[\-0-9a-z]+)$', IssuerDetail.as_view(), name='issuer_detail'),
   url(r'^/issuers/(?P<slug>[\-0-9a-z]+)/editors$', IssuerEditorsList.as_view(), name='issuer_editors'),
   url(r'^/issuers/(?P<slug>[\-0-9a-z]+)/staff$', IssuerStaffList.as_view(), name='issuer_staff'),

   url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges$', BadgeClassList.as_view(), name='badgeclass_list'),
   url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),

   url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions$', AssertionList.as_view(), name='assertion_list'),
   url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions/(?P<assertionSlug>[-\d\w]+)$', AssertionDetail.as_view(), name='assertion_detail'),
)
