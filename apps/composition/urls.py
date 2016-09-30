from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import CollectionDetailView, CollectionDetailEmbedView, EarnerPortal, LegacyCollectionShareRedirectView

urlpatterns = patterns('earner.views',
    url(r'^/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection'),
    url(r'^/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)/embed$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection_embed'),
    url(r'^', login_required(EarnerPortal.as_view()), name='earner_portal'),
)
