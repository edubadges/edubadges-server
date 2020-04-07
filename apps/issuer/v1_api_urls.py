from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BadgeInstanceDetail, BatchAssertionsIssue,
                        TimestampedBadgeInstanceList, BatchSignAssertions, IssuerBadgeClassList)

urlpatterns = [
    url(r'^badges/create$', IssuerBadgeClassList.as_view(), name='v1_api_badgeclass_list'),
    url(r'^issuers/(?P<slug>[^/]+)$', IssuerDetail.as_view(), name='v1_api_issuer_detail'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)$', BadgeClassDetail.as_view(), name='v1_api_badgeclass_detail'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)/batchAssertions$', BatchAssertionsIssue.as_view(), name='v1_api_badgeclass_batchissue'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<badgeSlug>[^/]+)/assertions/(?P<slug>[^/]+)$', BadgeInstanceDetail.as_view(), name='v1_api_badgeinstance_detail'),
    url(r'^batchSign$', BatchSignAssertions.as_view(), name='v1_api_batch_sign'),
    url(r'^timestamped-assertions$', TimestampedBadgeInstanceList.as_view(), name='v1_api_timestamped_badgeinstances'),
]
