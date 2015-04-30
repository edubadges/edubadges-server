from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from .api import (IssuerList, IssuerDetail, IssuerStaffList,
                  BadgeClassList, BadgeClassDetail, BadgeInstanceList,
                  BadgeInstanceDetail, IssuerBadgeInstanceList)


urlpatterns = patterns(
    'issuer.api_views',
    url(r'^$', RedirectView.as_view(url='/v1/issuer/issuers', permanent=False)),
    url(r'^/issuers$', IssuerList.as_view(), name='issuer_list'),
    url(r'^/issuers/(?P<slug>[-\w]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^/issuers/(?P<slug>[-\w]+)/staff$', IssuerStaffList.as_view(), name='issuer_staff'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/assertions$', IssuerBadgeInstanceList.as_view(), name='issuer_instance_list'),

    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges$', BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\d\w]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),

    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions$', BadgeInstanceList.as_view(), name='badgeinstance_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\d\w]+)/assertions/(?P<assertionSlug>[-\d\w]+)$', BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
)
