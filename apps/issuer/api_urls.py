from django.conf.urls import url

from issuer.api import (IssuerDetail, BadgeClassDetail, BatchAwardEnrollments,
                        TimestampedBadgeInstanceList, BatchSignAssertions, BadgeClassList, IssuerList,
                        IssuerDeleteView, BadgeClassDeleteView, BadgeInstanceRevoke, BadgeInstanceCollectionDetail,
                        BadgeInstanceCollectionDetailList, BadgeClassArchiveView)

urlpatterns = [
    url(r'^create$', IssuerList.as_view(), name='issuer_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', IssuerDetail.as_view(), name='issuer_detail'),
    url(r'^delete/(?P<entity_id>[^/]+)$', IssuerDeleteView.as_view(), name='issuer_delete'),
    url(r'^badgeclasses/create$',
        BadgeClassList.as_view(), name='badgeclass_list'),
    url(r'^badgeclasses/edit/(?P<entity_id>[^/]+)$',
        BadgeClassDetail.as_view(), name='badgeclass_detail'),
    url(r'^badgeclasses/delete/(?P<entity_id>[^/]+)$',
        BadgeClassDeleteView.as_view(), name='badgeclass_delete'),
    url(r'^badgeclasses/archive/(?P<entity_id>[^/]+)$',
        BadgeClassArchiveView.as_view(), name='badgeclass_archive'),
    url(r'^badgeclasses/award-enrollments/(?P<entity_id>[^/]+)$',
        BatchAwardEnrollments.as_view(), name='badgeclass_award_enrollments'),
    url(r'^revoke-assertions$', BadgeInstanceRevoke.as_view(), name='badgeinstance_revoke'),
    url(r'^batchSign$',
        BatchSignAssertions.as_view(), name='batch_sign'),
    url(r'^timestamped-assertions$',
        TimestampedBadgeInstanceList.as_view(), name='timestamped_badgeinstances'),
    url(r'^collections/create$', BadgeInstanceCollectionDetailList.as_view(), name='badge_collection_create'),
    url(r'^collections/edit/(?P<entity_id>[^/]+)$', BadgeInstanceCollectionDetail.as_view(), name='badge_collection_edit'),
    url(r'^collections/delete/(?P<entity_id>[^/]+)$', BadgeInstanceCollectionDetail.as_view(), name='badge_collection_delete'),

]
