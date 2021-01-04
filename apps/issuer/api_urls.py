from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BadgeInstanceDetail, BatchAwardEnrollments,
                        TimestampedBadgeInstanceList, BatchSignAssertions, BadgeClassList,
                        IssuerList, IssuerArchiveView, BadgeClassArchiveView)

urlpatterns = [
    url(r'^create$', IssuerList.as_view(), name='issuer_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^archive/(?P<entity_id>[^/]+)$', IssuerArchiveView.as_view(), name='issuer_detail'),
    url(r'^badgeclasses/create$',
        BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^badgeclasses/edit/(?P<entity_id>[^/]+)$',
        BadgeClassDetail.as_view(), name='badgeclass_detail'),
    url(r'^badgeclasses/archive/(?P<entity_id>[^/]+)$',
        BadgeClassArchiveView.as_view(), name='badgeclass_detail'),
    url(r'^badgeclasses/award-enrollments/(?P<entity_id>[^/]+)$',
        BatchAwardEnrollments.as_view(), name='badgeclass_award_enrollments'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<badgeSlug>[^/]+)/assertions/(?P<entity_id>[^/]+)$',
        BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
    url(r'^batchSign$',
        BatchSignAssertions.as_view(), name='batch_sign'),
    url(r'^timestamped-assertions$',
        TimestampedBadgeInstanceList.as_view(), name='timestamped_badgeinstances'),
]
