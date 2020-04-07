from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BadgeInstanceDetail, BatchAssertionsIssue,
                        TimestampedBadgeInstanceList, BatchSignAssertions, BadgeClassList,
                        IssuerList)

urlpatterns = [
    url(r'^badges/create$', BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^issuers/create$', IssuerList.as_view(), name='issuer_list'),
    url(r'^issuers/(?P<slug>[^/]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)/batchAssertions$', BatchAssertionsIssue.as_view(), name='badgeclass_batchissue'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<badgeSlug>[^/]+)/assertions/(?P<slug>[^/]+)$', BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
    url(r'^batchSign$', BatchSignAssertions.as_view(), name='batch_sign'),
    url(r'^timestamped-assertions$', TimestampedBadgeInstanceList.as_view(), name='timestamped_badgeinstances'),
]
