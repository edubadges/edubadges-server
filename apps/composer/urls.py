from django.conf.urls import patterns, url
from views import CollectionDetailView, CollectionDetailEmbedView, EarnerPortal

urlpatterns = patterns('earner.views',
    url(r'^/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)$', CollectionDetailView.as_view(), name='shared_collection'),
    url(r'^/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)/embed$', CollectionDetailEmbedView.as_view(), name='shared_collection_embed'),
    url(r'^', EarnerPortal.as_view(), name='earner_portal'),
)
