from django.conf.urls import url

from issuer.api import (IssuerList, IssuerDetail, IssuerBadgeClassList, BadgeClassDetail, BadgeInstanceList,
                        BadgeInstanceDetail, IssuerBadgeInstanceList, AllBadgeClassesList, BatchAssertionsIssue,
                        BatchAssertionsRevoke, IssuerTokensList, AssertionsChangedSince)

urlpatterns = [

    url(r'^issuers$', IssuerList.as_view(), name='v2_api_issuer_list'),
    url(r'^issuers/(?P<entity_id>[^/]+)$', IssuerDetail.as_view(), name='v2_api_issuer_detail'),
    url(r'^issuers/(?P<entity_id>[^/]+)/assertions$', IssuerBadgeInstanceList.as_view(), name='v2_api_issuer_assertion_list'),
    url(r'^issuers/(?P<entity_id>[^/]+)/badgeclasses$', IssuerBadgeClassList.as_view(), name='v2_api_issuer_badgeclass_list'),

    url(r'^badgeclasses$', AllBadgeClassesList.as_view(), name='v2_api_badgeclass_list'),
    url(r'^badgeclasses/(?P<entity_id>[^/]+)$', BadgeClassDetail.as_view(), name='v2_api_badgeclass_detail'),
    url(r'^badgeclasses/(?P<entity_id>[^/]+)/issue$', BatchAssertionsIssue.as_view(), name='v2_api_badgeclass_issue'),
    url(r'^badgeclasses/(?P<entity_id>[^/]+)/assertions$', BadgeInstanceList.as_view(), name='v2_api_badgeclass_assertion_list'),

    url(r'^assertions/revoke$', BatchAssertionsRevoke.as_view(), name='v2_api_assertion_revoke'),
    url(r'^assertions/changed$', AssertionsChangedSince.as_view(), name='v2_api_assertions_changed_list'),
    url(r'^assertions/(?P<entity_id>[^/]+)$', BadgeInstanceDetail.as_view(), name='v2_api_assertion_detail'),

    url(r'^tokens/issuers$', IssuerTokensList.as_view(), name='v2_api_tokens_list'),
]
