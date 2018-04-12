from django.conf.urls import url

from backpack.views import LegacyBadgeShareRedirectView, RedirectSharedCollectionView, LegacyCollectionShareRedirectView

urlpatterns = [
    # legacy redirects

    url(r'^share/?collection/(?P<share_hash>[^/]+)(/embed)?$', RedirectSharedCollectionView.as_view(), name='redirect_backpack_shared_collection'),
    url(r'^share/?badge/(?P<share_hash>[^/]+)$', LegacyBadgeShareRedirectView.as_view(), name='legacy_redirect_backpack_shared_badge'),

    url(r'^earner/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection'),
    url(r'^earner/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)/embed$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection_embed'),
]

