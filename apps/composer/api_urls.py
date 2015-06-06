from django.conf.urls import patterns, url

from .api import *

urlpatterns = patterns(
    'issuer.api_views',
    url(r'^/badges$', EarnerBadgeList.as_view(), name='earner_badge_list'),
    url(r'^/badges/(?P<badge_id>[\d]+)$', EarnerBadgeDetail.as_view(), name='earner_badge_detail'),
    url(r'^/collections$', EarnerCollectionList.as_view(), name='earner_collection_list'),
    url(r'^/collections/(?P<slug>[-\w]+)$', EarnerCollectionDetail.as_view(), name='earner_collection_detail'),
    url(r'^/collections/(?P<slug>[-\w]+)/badges$', EarnerCollectionBadgesList.as_view(), name='earner_collection_badges'),
    url(r'^/collections/(?P<collection_slug>[-\w]+)/badges/(?P<badge_id>[\d]+)$', EarnerCollectionBadgeDetail.as_view(), name='earner_collection_badge_detail'),
    url(r'^/collections/(?P<slug>[-\w]+)/share$', EarnerCollectionGenerateShare.as_view(), name='earner_collection_generate_share'),
)
