from django.urls import path

from backpack.api import (
    BackpackAssertionList,
    BackpackAssertionDetail,
    BackpackAssertionDetailImage,
    ShareBackpackAssertion,
)

urlpatterns = [
    path('badges', BackpackAssertionList.as_view(), name='v1_api_localbadgeinstance_list'),
    path('badges/<str:entity_id>', BackpackAssertionDetail.as_view(), name='v1_api_localbadgeinstance_detail'),
    path(
        'badges/<str:entity_id>/image', BackpackAssertionDetailImage.as_view(), name='v1_api_localbadgeinstance_image'
    ),
    # legacy v1 endpoints
    path('share/badge/<str:entity_id>', ShareBackpackAssertion.as_view(), name='v1_api_analytics_share_badge'),
]
