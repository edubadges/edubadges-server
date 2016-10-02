from django.conf.urls import url

from composition.views import CollectionDetailEmbedView, CollectionDetailView, SharedBadgeView

urlpatterns = [
    url('^/badge/(?P<badge_id>[^/]+)$', SharedBadgeView.as_view(), name='shared_badge'),

    url(r'^/collection/(?P<share_hash>[^/]+)$', CollectionDetailView.as_view(), name='shared_collection'),
    url(r'^/collection/(?P<share_hash>[^/]+)/embed$', CollectionDetailEmbedView.as_view(), name='shared_collection_embed'),
]