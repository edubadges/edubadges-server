from backpack.api import (
    BackpackAssertionDetail,
    BackpackAssertionDetailImage,
    BackpackAwardDetail,
    ShareBackpackAssertion,
)
from django.urls import path

urlpatterns = [
    path("awards/<str:entity_id>", BackpackAwardDetail.as_view(), name="v1_api_award_detail"),
    path("badges/<str:entity_id>", BackpackAssertionDetail.as_view(), name="v1_api_localbadgeinstance_detail"),
    path(
        "badges/<str:entity_id>/image", BackpackAssertionDetailImage.as_view(), name="v1_api_localbadgeinstance_image"
    ),
    # legacy v1 endpoints
    path("share/badge/<str:entity_id>", ShareBackpackAssertion.as_view(), name="v1_api_analytics_share_badge"),
]
