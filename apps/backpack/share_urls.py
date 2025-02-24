from django.urls import path

from backpack.views import LegacyBadgeShareRedirectView

urlpatterns = [
    # legacy redirects
    path(
        'share/badge/<str:entity_id>',
        LegacyBadgeShareRedirectView.as_view(),
        name='legacy_redirect_backpack_shared_badge',
    ),
]
