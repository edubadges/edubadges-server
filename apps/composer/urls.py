from django.conf.urls import patterns, url
from views import CollectionDetailView, EarnerPortal

urlpatterns = patterns('earner.views',
    url(r'^/earner$', EarnerPortal.as_view(), name='earner_portal'),
    url(r'^/collection/(?P<slug>[-\w]+)/(?P<share_hash>[^/]+)$', CollectionDetailView.as_view(), name='shared_collection'),
)
