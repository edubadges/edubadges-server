from django.conf.urls import patterns, url

from .api import (IssuerList, IssuerDetail, IssuerStaffList,
                  BadgeClassList, BadgeClassDetail, BadgeInstanceList,
                  BadgeInstanceDetail)


urlpatterns = patterns(
    'issuer.api_views',
    url(r'^/issuers$', IssuerList.as_view(), name='issuer_list'),
    url(r'^/issuers/(?P<slug>[\-0-9a-z]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^/issuers/(?P<slug>[\-0-9a-z]+)/staff$', IssuerStaffList.as_view(), name='issuer_staff'),

    url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges$', BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),

    url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions$', BadgeInstanceList.as_view(), name='badgeinstance_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\d\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions/(?P<assertionSlug>[-\d\w]+)$', BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
)
