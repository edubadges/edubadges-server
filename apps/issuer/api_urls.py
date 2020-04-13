from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BadgeInstanceDetail, BatchAwardEnrollments,
                        TimestampedBadgeInstanceList, BatchSignAssertions, BadgeClassList,
                        IssuerList)

urlpatterns = [
    url(r'^create$', IssuerList.as_view(), name='issuer_list'),
    url(r'^edit/(?P<slug>[^/]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^badgeclasses/create$', BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^badgeclasses/edit/(?P<slug>[^/]+)$', BadgeClassDetail.as_view(), name='badgeclass_detail'),

    url(r'^badgeclasses/award-enrollments/(?P<slug>[^/]+)$', BatchAwardEnrollments.as_view(), name='badgeclass_award_enrollments'),
    url(r'^issuers/(?P<issuerSlug>[^/]+)/badges/(?P<badgeSlug>[^/]+)/assertions/(?P<slug>[^/]+)$', BadgeInstanceDetail.as_view(), name='badgeinstance_detail'),
    url(r'^batchSign$', BatchSignAssertions.as_view(), name='batch_sign'),
    url(r'^timestamped-assertions$', TimestampedBadgeInstanceList.as_view(), name='timestamped_badgeinstances'),
]
