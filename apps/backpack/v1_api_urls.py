from backpack.api import (
    BackpackAssertionList,
    BackpackAssertionDetail,
    BackpackAssertionDetailImage,
    ShareBackpackAssertion,
    ImportedAssertionList,
    ImportedAssertionDetail,
    ImportedAssertionDelete,
    ImportedAssertionValidate,
)
from django.urls import path

urlpatterns = [
    path("badges", BackpackAssertionList.as_view(), name="v1_api_localbadgeinstance_list"),
    path("badges/<str:entity_id>", BackpackAssertionDetail.as_view(), name="v1_api_localbadgeinstance_detail"),
    path(
        "badges/<str:entity_id>/image", BackpackAssertionDetailImage.as_view(), name="v1_api_localbadgeinstance_image"
    ),
    # legacy v1 endpoints
    path("share/badge/<str:entity_id>", ShareBackpackAssertion.as_view(), name="v1_api_analytics_share_badge"),
    # imported assertions
    path("imported/assertions", ImportedAssertionList.as_view(), name="api_imported_assertions_list"),
    path(
        "imported/assertions/detail/<str:entity_id>",
        ImportedAssertionDetail.as_view(),
        name="api_imported_assertion_detail",
    ),
    path(
        "imported/assertions/edit/<str:entity_id>",
        ImportedAssertionDetail.as_view(),
        name="api_imported_assertions_edit",
    ),
    path(
        "imported/assertions/delete/<str:entity_id>",
        ImportedAssertionDelete.as_view(),
        name="api_imported_assertions_delete",
    ),
    path(
        "imported/assertions/validate/<str:entity_id>",
        ImportedAssertionValidate.as_view(),
        name="imported_assertion_validate",
    ),
]
