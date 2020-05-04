from backpack.views import LegacyBadgeShareRedirectView
from django.conf.urls import url

urlpatterns = [
    # legacy redirects
    url(r'^share/?badge/(?P<share_hash>[^/]+)$', LegacyBadgeShareRedirectView.as_view(), name='legacy_redirect_backpack_shared_badge'),
]

