from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from composition.views import CollectionDetailEmbedView, CollectionDetailView, SharedBadgeView

urlpatterns = [
    url(r'^/badge/(?P<share_hash>[^/]+)$', SharedBadgeView.as_view(), name='backpack_shared_assertion'),
    url(r'^/collection/(?P<share_hash>[^/]+)$', CollectionDetailView.as_view(), name='backpack_shared_collection'),
    url(r'^/collection/(?P<share_hash>[^/]+)/embed$', CollectionDetailEmbedView.as_view(), name='backpack_shared_collection_embed'),
]

# urlpatterns = format_suffix_patterns(json_patterns, allowed=['json', 'html']) + html_patterns
