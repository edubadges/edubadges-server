from backpack.views import LegacyBadgeShareRedirectView
from django.urls import path

urlpatterns = [
    # legacy redirects
    path(
        "share/badge/<str:entity_id>",
        LegacyBadgeShareRedirectView.as_view(),
        name="legacy_redirect_backpack_shared_badge",
    ),
]
