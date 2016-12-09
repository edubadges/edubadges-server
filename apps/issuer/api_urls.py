from django.conf.urls import patterns, url
from django.views.generic.base import RedirectView

from .api import (IssuerList, IssuerDetail, IssuerStaffList,
                  BadgeClassList, BadgeClassDetail, BadgeInstanceList,
                  BadgeInstanceDetail, IssuerBadgeInstanceList,
                  AllBadgeClassesList, BatchAssertions)


urlpatterns = patterns(
    'issuer.api_views',
    url(r'^$', RedirectView.as_view(url='/v1/issuer/issuers', permanent=False)),
    url(r'^/all-badges$', AllBadgeClassesList.as_view(), name='issuer_all_badges_list'),
    url(r'^/issuers$', IssuerList.as_view(), name='issuer_list'),
    url(r'^/issuers/(?P<slug>[-\w]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^/issuers/(?P<slug>[-\w]+)/staff$', IssuerStaffList.as_view(), name='issuer_staff'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/assertions$', IssuerBadgeInstanceList.as_view(), name='issuer_instance_list'),

    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges$', BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\w]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),

    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\w]+)/batchAssertions$', BatchAssertions.as_view(), name='badgeclass_batchissue'),

    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\w]+)/assertions$', BadgeInstanceList.as_view(), name='badgeinstance_list'),
    url(r'^/issuers/(?P<issuerSlug>[-\w]+)/badges/(?P<badgeSlug>[-\w]+)/assertions/(?P<assertionSlug>[-\w]+)$', BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
)
