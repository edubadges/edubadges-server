from django.conf.urls import url

from backpack.views import SharedCollectionView, EmbeddedSharedCollectionView, LegacyBadgeShareRedirectView

urlpatterns = [
    url(r'^/collection/(?P<share_hash>[^/]+)$', SharedCollectionView.as_view(), name='backpack_shared_collection'),
    url(r'^/collection/(?P<share_hash>[^/]+)/embed$', EmbeddedSharedCollectionView.as_view(), name='backpack_shared_collection_embed'),

    # legacy redirects
    url(r'^/badge/(?P<share_hash>[^/]+)$', LegacyBadgeShareRedirectView.as_view(), name='legacy_redirect_backpack_shared_badge'),
]

