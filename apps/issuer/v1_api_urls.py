from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BadgeInstanceList,
                        BadgeInstanceDetail, IssuerBadgeInstanceList, BatchAssertionsIssue,
                        TimestampedBadgeInstanceList, BatchSignAssertions)
from issuer.api_v1 import FindBadgeClassDetail

urlpatterns = [
    # url(r'^all-badges$', AllBadgeClassesList.as_view(), name='v1_api_issuer_all_badges_list'),
    url(r'^all-badges/find$', FindBadgeClassDetail.as_view(), name='v1_api_find_badgeclass_by_identifier'),

    # url(r'^issuers$', IssuerList.as_view(), name='v1_api_issuer_list'),
    url(r'^issuers/(?P<slug>[^/]+)$', IssuerDetail.as_view(), name='v1_api_issuer_detail'),
    # url(r'^issuers/(?P<slug>[^/]+)/staff$', IssuerStaffList.as_view(), name='v1_api_issuer_staff'),
    # url(r'^issuers-staff-confirm/(?P<code>[^/]+)$', IssuerStaffConfirm.as_view(), name='v1_api_issuer_staff_confirm'),

    # url(r'^issuers/(?P<slug>[^/]+)/badges$', IssuerBadgeClassList.as_view(), name='v1_api_badgeclass_list'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)$', BadgeClassDetail.as_view(), name='v1_api_badgeclass_detail'),

    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)/batchAssertions$', BatchAssertionsIssue.as_view(), name='v1_api_badgeclass_batchissue'),

    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<slug>[^/]+)/assertions$', BadgeInstanceList.as_view(), name='v1_api_badgeinstance_list'),
    url(r'^issuers/(?P<slug>[^/]+)/assertions$', IssuerBadgeInstanceList.as_view(), name='v1_api_issuer_instance_list'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<badgeSlug>[^/]+)/assertions/(?P<slug>[^/]+)$', BadgeInstanceDetail.as_view(), name='v1_api_badgeinstance_detail'),

    url(r'^batchSign$', BatchSignAssertions.as_view(), name='v1_api_batch_sign'),
    url(r'^timestamped-assertions$', TimestampedBadgeInstanceList.as_view(), name='v1_api_timestamped_badgeinstances'),
]
