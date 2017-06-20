from django.conf.urls import url

from backpack.views import SharedCollectionView, EmbeddedSharedCollectionView

urlpatterns = [
    url(r'^/collection/(?P<share_hash>[^/]+)$', SharedCollectionView.as_view(), name='backpack_shared_collection'),
    url(r'^/collection/(?P<share_hash>[^/]+)/embed$', EmbeddedSharedCollectionView.as_view(), name='backpack_shared_collection_embed'),
]

