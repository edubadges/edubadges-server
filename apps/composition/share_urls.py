from django.conf.urls import url

from rest_framework.urlpatterns import format_suffix_patterns

from composition.views import CollectionDetailEmbedView, CollectionDetailView, SharedBadgeView


json_patterns = [
    url('^/badge/(?P<badge_id>[^/^\.]+)$', SharedBadgeView.as_view(), name='shared_badge'),
]

html_patterns = [
    url(r'^/collection/(?P<share_hash>[^/]+)$', CollectionDetailView.as_view(), name='shared_collection'),
    url(r'^/collection/(?P<share_hash>[^/]+)/embed$', CollectionDetailEmbedView.as_view(), name='shared_collection_embed'),
]

urlpatterns = format_suffix_patterns(json_patterns, allowed=['json', 'html']) + html_patterns
