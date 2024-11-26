from django.urls import path

from issuer.api import (
    IssuerDetail,
    BadgeClassDetail,
    BatchAwardEnrollments,
    TimestampedBadgeInstanceList,
    BatchSignAssertions,
    BadgeClassList,
    IssuerList,
    IssuerDeleteView,
    BadgeClassDeleteView,
    BadgeInstanceRevoke,
    BadgeInstanceCollectionDetail,
    BadgeInstanceCollectionDetailList,
    BadgeClassArchiveView,
)

urlpatterns = [
    path("create", IssuerList.as_view(), name="issuer_list"),
    path("edit/<str:entity_id>", IssuerDetail.as_view(), name="issuer_detail"),
    path("delete/<str:entity_id>", IssuerDeleteView.as_view(), name="issuer_delete"),
    path("badgeclasses/create", BadgeClassList.as_view(), name="badgeclass_list"),
    path("badgeclasses/edit/<str:entity_id>", BadgeClassDetail.as_view(), name="badgeclass_detail"),
    path("badgeclasses/delete/<str:entity_id>", BadgeClassDeleteView.as_view(), name="badgeclass_delete"),
    path("badgeclasses/archive/<str:entity_id>", BadgeClassArchiveView.as_view(), name="badgeclass_archive"),
    path(
        "badgeclasses/award-enrollments/<str:entity_id>",
        BatchAwardEnrollments.as_view(),
        name="badgeclass_award_enrollments",
    ),
    path("revoke-assertions", BadgeInstanceRevoke.as_view(), name="badgeinstance_revoke"),
    path("batchSign", BatchSignAssertions.as_view(), name="batch_sign"),
    path("timestamped-assertions", TimestampedBadgeInstanceList.as_view(), name="timestamped_badgeinstances"),
    path("collections/create", BadgeInstanceCollectionDetailList.as_view(), name="badge_collection_create"),
    path("collections/edit/<str:entity_id>", BadgeInstanceCollectionDetail.as_view(), name="badge_collection_edit"),
    path("collections/delete/<str:entity_id>", BadgeInstanceCollectionDetail.as_view(), name="badge_collection_delete"),
]
